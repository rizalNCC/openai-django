from django.shortcuts import redirect, render

from .forms import AgentProfileForm, AgentToolForm
from .models import AgentProfile, AgentSession, AgentTool


def admin_dashboard(request):
    agent_form = AgentProfileForm(prefix="agent")
    tool_form = AgentToolForm(prefix="tool")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_agent":
            agent_form = AgentProfileForm(request.POST, prefix="agent")
            if agent_form.is_valid():
                agent_form.save()
                return redirect("admin-dashboard")
        elif action == "create_tool":
            tool_form = AgentToolForm(request.POST, prefix="tool")
            if tool_form.is_valid():
                tool_form.save()
                return redirect("admin-dashboard")

    context = {
        "agent_count": AgentProfile.objects.count(),
        "tool_count": AgentTool.objects.count(),
        "session_count": AgentSession.objects.count(),
        "agents": AgentProfile.objects.order_by("-updated_at")[:10],
        "tools": AgentTool.objects.order_by("-created_at")[:10],
        "recent_sessions": AgentSession.objects.select_related("agent", "owner")
        .order_by("-updated_at")[:5],
        "agent_form": agent_form,
        "tool_form": tool_form,
    }
    return render(request, "admin_dashboard.html", context)


def message_playground(request):
    context = {
        "agents": AgentProfile.objects.order_by("name"),
    }
    return render(request, "message_playground.html", context)
