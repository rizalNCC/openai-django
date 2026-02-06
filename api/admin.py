from django.contrib import admin

from .models import (
    AgentMessage,
    AgentProfile,
    AgentProfileTool,
    AgentPromptTemplate,
    AgentSession,
    AgentTool,
)


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "model", "is_default", "owner", "created_at")
    list_filter = ("is_default", "model")
    search_fields = ("name", "model")


@admin.register(AgentTool)
class AgentToolAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "tool_type", "is_active", "created_at")
    list_filter = ("tool_type", "is_active")
    search_fields = ("name",)


@admin.register(AgentProfileTool)
class AgentProfileToolAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "tool", "enabled")
    list_filter = ("enabled",)


@admin.register(AgentPromptTemplate)
class AgentPromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "agent", "owner", "is_default", "created_at")
    list_filter = ("is_default",)
    search_fields = ("name",)


@admin.register(AgentSession)
class AgentSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "owner", "created_at", "updated_at")
    search_fields = ("id",)


@admin.register(AgentMessage)
class AgentMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "created_at")
    search_fields = ("content",)

# Register your models here.
