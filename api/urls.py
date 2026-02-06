from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AgentProfileViewSet,
    AgentStreamView,
    AgentToolOutputView,
    AgentToolViewSet,
    ChatView,
)

router = DefaultRouter()
router.register(r"agents", AgentProfileViewSet, basename="agent-profile")
router.register(r"tools", AgentToolViewSet, basename="agent-tool")

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("agent/stream/", AgentStreamView.as_view(), name="agent-stream"),
    path("agent/tool-output/", AgentToolOutputView.as_view(), name="agent-tool-output"),
    path("", include(router.urls)),
]
