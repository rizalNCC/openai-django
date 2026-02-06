import json
from typing import Any, Dict, Iterable, List, Optional

import openai
from django.conf import settings
from django.http import StreamingHttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AgentProfile, AgentProfileTool, AgentSession, AgentTool
from .serializers import (
    AgentChatRequestSerializer,
    AgentProfileSerializer,
    AgentStreamRequestSerializer,
    AgentToolOutputSerializer,
    AgentToolSerializer,
)
from .tools import tool_registry


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _event_to_dict(event: Any) -> Dict[str, Any]:
    if isinstance(event, dict):
        return event
    if hasattr(event, "model_dump"):
        return event.model_dump()
    if hasattr(event, "__dict__"):
        return event.__dict__
    return {"type": "unknown", "data": str(event)}


def _normalize_output_items(output: Any) -> List[Dict[str, Any]]:
    if output is None:
        return []
    items = output if isinstance(output, list) else list(output)
    normalized = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(item)
        elif hasattr(item, "model_dump"):
            normalized.append(item.model_dump())
        elif hasattr(item, "__dict__"):
            normalized.append(item.__dict__)
        else:
            normalized.append({"type": "unknown", "data": str(item)})
    return normalized

def _get_or_create_agent(user, agent_id: Optional[int]) -> AgentProfile:
    if agent_id:
        return AgentProfile.objects.get(id=agent_id)
    default_agent = AgentProfile.objects.filter(is_default=True).first()
    if default_agent:
        return default_agent
    return AgentProfile.objects.create(
        name="Default Agent",
        owner=user if getattr(user, "is_authenticated", False) else None,
        model="gpt-4.1",
        system_prompt="You are a helpful assistant.",
        is_default=True,
    )


def _build_tools(agent: AgentProfile) -> list:
    tool_links = (
        AgentProfileTool.objects.filter(agent=agent, enabled=True, tool__is_active=True)
        .select_related("tool")
        .all()
    )
    if tool_links:
        tools = [link.tool for link in tool_links]
    else:
        tools = []

    tool_defs = []
    for tool in tools:
        if tool.tool_type == "function":
            tool_defs.append(
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters or {},
                }
            )
        elif tool.tool_type == "custom":
            tool_defs.append(
                {
                    "type": "custom",
                    "name": tool.name,
                    "description": tool.description,
                }
            )
    return tool_defs


class AgentProfileViewSet(viewsets.ModelViewSet):
    queryset = AgentProfile.objects.all().order_by("id")
    serializer_class = AgentProfileSerializer


class AgentToolViewSet(viewsets.ModelViewSet):
    queryset = AgentTool.objects.all().order_by("id")
    serializer_class = AgentToolSerializer


class AgentStreamView(APIView):
    @swagger_auto_schema(request_body=AgentStreamRequestSerializer)
    def post(self, request):
        serializer = AgentStreamRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.validated_data["message"]
        agent_id = serializer.validated_data.get("agent_id")
        session_id = serializer.validated_data.get("session_id")
        auto_execute_tools = serializer.validated_data.get("auto_execute_tools", False)

        try:
            agent = _get_or_create_agent(request.user, agent_id)
        except AgentProfile.DoesNotExist:
            return Response({"error": "Agent not found."}, status=status.HTTP_404_NOT_FOUND)

        if session_id:
            try:
                session = AgentSession.objects.get(id=session_id, agent=agent)
            except AgentSession.DoesNotExist:
                return Response(
                    {"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            session = AgentSession.objects.create(
                agent=agent,
                owner=request.user if request.user.is_authenticated else None,
            )

        session.messages.create(role="user", content=message)

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        tools = _build_tools(agent)

        def _run_stream(input_items: List[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
            response_stream = client.responses.create(
                model=agent.model,
                instructions=agent.system_prompt or None,
                input=input_items,
                tools=tools,
                previous_response_id=session.previous_response_id or None,
                stream=True,
            )
            for event in response_stream:
                yield _event_to_dict(event)

        def event_stream() -> Iterable[str]:
            output_text_parts: List[str] = []
            all_text_parts: List[str] = []
            completed_response: Optional[Dict[str, Any]] = None
            tool_calls: Dict[str, Dict[str, Any]] = {}
            max_rounds = 3

            pending_inputs = [{"role": "user", "content": message}]
            while max_rounds > 0:
                max_rounds -= 1
                for event_dict in _run_stream(pending_inputs):
                    yield _sse_event("openai_event", event_dict)

                    if event_dict.get("type") == "response.output_text.delta":
                        delta = event_dict.get("delta") or ""
                        if delta:
                            output_text_parts.append(delta)
                            all_text_parts.append(delta)
                            yield _sse_event("text_delta", {"delta": delta})

                    if event_dict.get("type") == "response.output_item.added":
                        item = event_dict.get("item") or {}
                        if item.get("type") == "function_call":
                            call_id = item.get("call_id")
                            if call_id:
                                tool_calls[call_id] = {
                                    "id": item.get("id"),
                                    "name": item.get("name"),
                                    "arguments": item.get("arguments", ""),
                                }

                    if event_dict.get("type") == "response.function_call_arguments.delta":
                        item_id = event_dict.get("item_id")
                        for call_id, data in tool_calls.items():
                            if data.get("id") == item_id:
                                data["arguments"] = (data.get("arguments") or "") + (
                                    event_dict.get("delta") or ""
                                )
                                break

                    if event_dict.get("type") == "response.function_call_arguments.done":
                        item_id = event_dict.get("item_id")
                        for call_id, data in tool_calls.items():
                            if data.get("id") == item_id:
                                data["arguments"] = event_dict.get("arguments") or ""
                                break

                    if event_dict.get("type") == "response.completed":
                        completed_response = event_dict.get("response")

                if completed_response:
                    session.previous_response_id = completed_response.get("id", "")
                    session.last_output = completed_response.get("output", [])
                    session.save(
                        update_fields=["previous_response_id", "last_output", "updated_at"]
                    )

                if not auto_execute_tools or not tool_calls:
                    break

                tool_outputs = []
                for call_id, data in tool_calls.items():
                    name = data.get("name")
                    arguments = data.get("arguments", "")
                    if not name or not tool_registry.has(name):
                        continue
                    try:
                        result = tool_registry.execute(name, arguments)
                    except Exception as exc:
                        result = json.dumps({"error": str(exc)})
                    tool_outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": result,
                        }
                    )

                if not tool_outputs:
                    break

                tool_calls = {}
                pending_inputs = tool_outputs
                output_text_parts = []

            final_text = "".join(all_text_parts).strip()
            if final_text:
                session.messages.create(role="assistant", content=final_text)

            yield _sse_event("done", {"session_id": session.id})

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class AgentToolOutputView(APIView):
    @swagger_auto_schema(request_body=AgentToolOutputSerializer)
    def post(self, request):
        serializer = AgentToolOutputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = AgentSession.objects.get(id=serializer.validated_data["session_id"])
        except AgentSession.DoesNotExist:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)
        call_id = serializer.validated_data["call_id"]
        output = serializer.validated_data["output"]

        agent = session.agent
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        tools = _build_tools(agent)

        tool_output_item = {
            "type": "function_call_output",
            "call_id": call_id,
            "output": output,
        }

        stream = client.responses.create(
            model=agent.model,
            instructions=agent.system_prompt or None,
            input=[tool_output_item],
            tools=tools,
            previous_response_id=session.previous_response_id or None,
            stream=True,
        )

        def event_stream() -> Iterable[str]:
            output_text_parts = []
            completed_response = None
            for event in stream:
                event_dict = _event_to_dict(event)
                yield _sse_event("openai_event", event_dict)

                if event_dict.get("type") == "response.output_text.delta":
                    delta = event_dict.get("delta") or ""
                    if delta:
                        output_text_parts.append(delta)
                        yield _sse_event("text_delta", {"delta": delta})

                if event_dict.get("type") == "response.completed":
                    completed_response = event_dict.get("response")

            if completed_response:
                session.previous_response_id = completed_response.get("id", "")
                session.last_output = completed_response.get("output", [])
                session.save(
                    update_fields=["previous_response_id", "last_output", "updated_at"]
                )

            final_text = "".join(output_text_parts).strip()
            if final_text:
                session.messages.create(role="assistant", content=final_text)

            yield _sse_event("done", {"session_id": session.id})

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class AgentChatView(APIView):
    @swagger_auto_schema(request_body=AgentChatRequestSerializer)
    def post(self, request):
        serializer = AgentChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.validated_data["message"]
        agent_id = serializer.validated_data.get("agent_id")
        session_id = serializer.validated_data.get("session_id")

        try:
            agent = _get_or_create_agent(request.user, agent_id)
        except AgentProfile.DoesNotExist:
            return Response({"error": "Agent not found."}, status=status.HTTP_404_NOT_FOUND)

        if session_id:
            try:
                session = AgentSession.objects.get(id=session_id, agent=agent)
            except AgentSession.DoesNotExist:
                return Response(
                    {"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            session = AgentSession.objects.create(
                agent=agent,
                owner=request.user if request.user.is_authenticated else None,
            )

        session.messages.create(role="user", content=message)

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        tools = _build_tools(agent)

        response = client.responses.create(
            model=agent.model,
            instructions=agent.system_prompt or None,
            input=[{"role": "user", "content": message}],
            tools=tools,
            previous_response_id=session.previous_response_id or None,
        )

        output_text = ""
        if hasattr(response, "output_text"):
            output_text = response.output_text
        normalized_output = _normalize_output_items(getattr(response, "output", []))
        if not output_text:
            for item in normalized_output:
                if item.get("type") == "message":
                    for part in item.get("content", []):
                        if part.get("type") == "output_text":
                            output_text += part.get("text", "")

        tool_calls = []
        for item in normalized_output:
            if item.get("type") == "function_call":
                tool_calls.append(
                    {
                        "call_id": item.get("call_id"),
                        "name": item.get("name"),
                        "arguments": item.get("arguments"),
                    }
                )

        session.previous_response_id = getattr(response, "id", "") or ""
        session.last_output = normalized_output
        session.save(update_fields=["previous_response_id", "last_output", "updated_at"])

        if output_text:
            session.messages.create(role="assistant", content=output_text)

        payload = {"session_id": session.id, "response": output_text}
        if tool_calls:
            payload["tool_calls"] = tool_calls
        return Response(payload, status=status.HTTP_200_OK)
