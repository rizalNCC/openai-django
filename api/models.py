from django.conf import settings
from django.db import models


class AgentProfile(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="agent_profiles",
    )
    model = models.CharField(max_length=100, default="gpt-4.1")
    system_prompt = models.TextField(blank=True, default="")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class AgentTool(models.Model):
    TOOL_TYPE_FUNCTION = "function"
    TOOL_TYPE_CUSTOM = "custom"

    TOOL_TYPE_CHOICES = [
        (TOOL_TYPE_FUNCTION, "Function"),
        (TOOL_TYPE_CUSTOM, "Custom"),
    ]

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, default="")
    tool_type = models.CharField(max_length=20, choices=TOOL_TYPE_CHOICES)
    parameters = models.JSONField(blank=True, default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class AgentProfileTool(models.Model):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE)
    tool = models.ForeignKey(AgentTool, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ("agent", "tool")


class AgentPromptTemplate(models.Model):
    name = models.CharField(max_length=200)
    template = models.TextField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="agent_prompt_templates",
    )
    agent = models.ForeignKey(
        AgentProfile,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="prompt_templates",
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class AgentSession(models.Model):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="agent_sessions",
    )
    previous_response_id = models.CharField(max_length=200, blank=True, default="")
    last_output = models.JSONField(blank=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AgentMessage(models.Model):
    session = models.ForeignKey(
        AgentSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
