from django import forms

from .models import AgentProfile, AgentTool

MODEL_CHOICES = [
    ("gpt-5-pro", "gpt-5-pro"),
    ("gpt-5-mini", "gpt-5-mini"),
    ("gpt-5-nano", "gpt-5-nano"),
    ("gpt-4o", "gpt-4o"),
    ("gpt-4o-mini", "gpt-4o-mini"),
    ("gpt-4.1", "gpt-4.1"),
    ("gpt-4.1-mini", "gpt-4.1-mini"),
    ("gpt-4.1-nano", "gpt-4.1-nano"),
    ("o3", "o3"),
    ("o3-mini", "o3-mini"),
    ("o4-mini", "o4-mini"),
    ("o1", "o1"),
    ("o1-mini", "o1-mini"),
    ("__custom__", "Custom (type below)"),
]


class AgentProfileForm(forms.ModelForm):
    model = forms.ChoiceField(choices=MODEL_CHOICES, required=True)
    custom_model = forms.CharField(
        required=False,
        help_text="Used only when model is set to Custom.",
    )

    class Meta:
        model = AgentProfile
        fields = ["name", "model", "system_prompt", "is_default"]

    def clean(self):
        cleaned = super().clean()
        model = cleaned.get("model")
        custom_model = (cleaned.get("custom_model") or "").strip()
        if model == "__custom__":
            if not custom_model:
                self.add_error("custom_model", "Please enter a custom model name.")
            else:
                cleaned["model"] = custom_model
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.model = self.cleaned_data["model"]
        if commit:
            instance.save()
        return instance


class AgentToolForm(forms.ModelForm):
    class Meta:
        model = AgentTool
        fields = ["name", "description", "tool_type", "parameters", "is_active"]
