from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AgentChatView,
    AgentProfileViewSet,
    AgentStreamView,
    AgentToolOutputView,
    AgentToolViewSet,
)

router = DefaultRouter()
router.register(r"agents", AgentProfileViewSet, basename="agent-profile")
router.register(r"tools", AgentToolViewSet, basename="agent-tool")

urlpatterns = [
    path("agent/chat/", AgentChatView.as_view(), name="agent-chat"),
    path("agent/stream/", AgentStreamView.as_view(), name="agent-stream"),
    path("agent/tool-output/", AgentToolOutputView.as_view(), name="agent-tool-output"),
    path("", include(router.urls)),
]
