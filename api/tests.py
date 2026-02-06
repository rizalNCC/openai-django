from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from .models import AgentProfile, AgentSession
from .tools import tool_registry


class AgentStreamTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.agent = AgentProfile.objects.create(
            name="Test Agent", model="gpt-4.1", system_prompt="Test"
        )

    def _stream_response(self, response):
        return b"".join(response.streaming_content).decode("utf-8")

    @patch("api.views.openai.OpenAI")
    def test_sse_event_forwarding(self, mock_openai):
        stream_events = [
            {"type": "response.output_text.delta", "delta": "Hi"},
            {"type": "response.completed", "response": {"id": "resp_1", "output": []}},
        ]
        mock_client = MagicMock()
        mock_client.responses.create.return_value = iter(stream_events)
        mock_openai.return_value = mock_client

        response = self.client.post(
            "/api/agent/stream/",
            {"message": "Hello", "agent_id": self.agent.id},
            format="json",
        )
        body = self._stream_response(response)

        self.assertIn("event: openai_event", body)
        self.assertIn("event: text_delta", body)
        self.assertIn("event: done", body)

    @patch("api.views.openai.OpenAI")
    def test_tool_call_detection_in_stream(self, mock_openai):
        stream_events = [
            {
                "type": "response.output_item.added",
                "item": {
                    "type": "function_call",
                    "id": "fc_1",
                    "call_id": "call_1",
                    "name": "echo",
                    "arguments": "",
                },
            },
            {"type": "response.completed", "response": {"id": "resp_2", "output": []}},
        ]
        mock_client = MagicMock()
        mock_client.responses.create.return_value = iter(stream_events)
        mock_openai.return_value = mock_client

        response = self.client.post(
            "/api/agent/stream/",
            {"message": "Trigger tool", "agent_id": self.agent.id},
            format="json",
        )
        body = self._stream_response(response)

        self.assertIn("response.output_item.added", body)

    @patch("api.views.openai.OpenAI")
    def test_auto_tool_execution_and_continuation(self, mock_openai):
        @tool_registry.register("echo")
        def _echo_tool(args):
            return {"echo": args.get("text")}

        first_stream = [
            {
                "type": "response.output_item.added",
                "item": {
                    "type": "function_call",
                    "id": "fc_1",
                    "call_id": "call_1",
                    "name": "echo",
                    "arguments": "",
                },
            },
            {
                "type": "response.function_call_arguments.done",
                "item_id": "fc_1",
                "arguments": "{\"text\": \"hi\"}",
            },
            {"type": "response.completed", "response": {"id": "resp_3", "output": []}},
        ]
        second_stream = [
            {"type": "response.output_text.delta", "delta": "Done"},
            {"type": "response.completed", "response": {"id": "resp_4", "output": []}},
        ]

        mock_client = MagicMock()
        mock_client.responses.create.side_effect = [iter(first_stream), iter(second_stream)]
        mock_openai.return_value = mock_client

        response = self.client.post(
            "/api/agent/stream/",
            {"message": "Auto tool", "agent_id": self.agent.id, "auto_execute_tools": True},
            format="json",
        )
        body = self._stream_response(response)

        self.assertGreaterEqual(mock_client.responses.create.call_count, 2)
        self.assertIn("Done", body)


class AgentToolOutputTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.agent = AgentProfile.objects.create(
            name="Test Agent", model="gpt-4.1", system_prompt="Test"
        )
        self.session = AgentSession.objects.create(agent=self.agent)

    def _stream_response(self, response):
        return b"".join(response.streaming_content).decode("utf-8")

    @patch("api.views.openai.OpenAI")
    def test_continuation_after_tool_output(self, mock_openai):
        stream_events = [
            {"type": "response.output_text.delta", "delta": "Result"},
            {"type": "response.completed", "response": {"id": "resp_5", "output": []}},
        ]
        mock_client = MagicMock()
        mock_client.responses.create.return_value = iter(stream_events)
        mock_openai.return_value = mock_client

        response = self.client.post(
            "/api/agent/tool-output/",
            {"session_id": self.session.id, "call_id": "call_9", "output": "ok"},
            format="json",
        )
        body = self._stream_response(response)

        self.assertIn("Result", body)
        self.assertIn("event: done", body)


class AgentChatTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.agent = AgentProfile.objects.create(
            name="Test Agent", model="gpt-4.1", system_prompt="Test"
        )

    @patch("api.views.openai.OpenAI")
    def test_agent_chat_non_streaming(self, mock_openai):
        response_obj = MagicMock()
        response_obj.id = "resp_10"
        response_obj.output = [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": "Hello there"}],
            }
        ]

        mock_client = MagicMock()
        mock_client.responses.create.return_value = response_obj
        mock_openai.return_value = mock_client

        response = self.client.post(
            "/api/agent/chat/",
            {"message": "Hi", "agent_id": self.agent.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "Hello there")
