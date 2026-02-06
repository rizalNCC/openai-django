from rest_framework import serializers

from .models import AgentProfile, AgentTool


class ChatSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, max_length=1000)


class AgentStreamRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, max_length=4000)
    agent_id = serializers.IntegerField(required=False)
    session_id = serializers.IntegerField(required=False)
    auto_execute_tools = serializers.BooleanField(required=False, default=False)


class AgentToolOutputSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=True)
    call_id = serializers.CharField(required=True, max_length=200)
    output = serializers.CharField(required=True)


class AgentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentProfile
        fields = [
            "id",
            "name",
            "owner",
            "model",
            "system_prompt",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AgentToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTool
        fields = [
            "id",
            "name",
            "description",
            "tool_type",
            "parameters",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
