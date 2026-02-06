from django.shortcuts import render

from .models import AgentProfile, AgentSession, AgentTool


def admin_dashboard(request):
    context = {
        "agent_count": AgentProfile.objects.count(),
        "tool_count": AgentTool.objects.count(),
        "session_count": AgentSession.objects.count(),
        "recent_sessions": AgentSession.objects.select_related("agent", "owner")
        .order_by("-updated_at")[:5],
    }
    return render(request, "admin_dashboard.html", context)
