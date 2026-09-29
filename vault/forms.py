from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Secret, User, Workspace, WorkspaceMember


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")


class SecretForm(forms.ModelForm):
    value = forms.CharField(
        label="Secret value",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "autocomplete": "off", "spellcheck": "false"}),
        help_text="Passwords, tokens or full private keys. Leave empty when editing to keep the current one.",
    )

    field_order = ["secret_type", "title", "username", "url", "value", "notes"]

    class Meta:
        model = Secret
        fields = ("secret_type", "title", "username", "url", "notes")
        labels = {"secret_type": "Type"}
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def clean_value(self):
        value = self.cleaned_data["value"].replace("\r\n", "\n")
        if not value.strip() and not self.instance.pk:
            raise forms.ValidationError("This field is required.")
        return value


class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ("name",)


class InviteForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=WorkspaceMember.ROLES)
