from django.contrib import messages
from django.contrib.auth import login, views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .audit import write_log
from .forms import InviteForm, RegisterForm, SecretForm, WorkspaceForm
from .models import AuditLog, Secret, User, Workspace, WorkspaceMember


def get_workspace(user, workspace_id):
    return get_object_or_404(Workspace, pk=workspace_id, workspacemember__user=user)


def is_admin(user, workspace):
    return WorkspaceMember.objects.filter(
        workspace=workspace, user=user, role=WorkspaceMember.ADMIN).exists()


def get_secret(user, pk):
    secrets = Secret.objects.filter(Q(owner=user) | Q(workspace__workspacemember__user=user))
    return get_object_or_404(secrets.distinct(), pk=pk)


def can_edit(user, secret):
    if secret.owner_id == user.id:
        return True
    return secret.workspace_id is not None and is_admin(user, secret.workspace)


def back_to_vault(workspace_id):
    if workspace_id:
        return redirect("workspace", workspace_id=workspace_id)
    return redirect("dashboard")


def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        write_log("REGISTER", user=user)
        login(request, user)
        return redirect("dashboard")
    return render(request, "register.html", {"form": form})


class PasswordChange(auth_views.PasswordChangeView):
    template_name = "form.html"
    extra_context = {"title": "Change password", "submit": "Update password"}
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        write_log("PASSWORD_CHANGE", user=self.request.user)
        return super().form_valid(form)


@login_required
def dashboard(request, workspace_id=None):
    if workspace_id:
        workspace = get_workspace(request.user, workspace_id)
        secrets = Secret.objects.filter(workspace=workspace)
        can_manage = is_admin(request.user, workspace)
    else:
        workspace = None
        secrets = Secret.objects.filter(owner=request.user)
        can_manage = True

    current_type = request.GET.get("type")
    if current_type in dict(Secret.TYPES):
        secrets = secrets.filter(secret_type=current_type)
    else:
        current_type = None

    return render(request, "dashboard.html", {
        "workspace": workspace,
        "secrets": secrets,
        "can_manage": can_manage,
        "types": Secret.TYPES,
        "current_type": current_type,
    })


@login_required
def secret_create(request, workspace_id=None):
    workspace = get_workspace(request.user, workspace_id) if workspace_id else None
    form = SecretForm(request.POST or None)
    if form.is_valid():
        secret = form.save(commit=False)
        secret.workspace = workspace
        secret.owner = None if workspace else request.user
        secret.set_value(form.cleaned_data["value"])
        secret.save()
        write_log("CREATE", user=request.user, secret=secret)
        messages.success(request, "Secret saved.")
        return back_to_vault(workspace_id)
    return render(request, "secret_form.html", {
        "form": form, "title": "Add a secret", "workspace": workspace})


@login_required
def secret_edit(request, pk):
    secret = get_secret(request.user, pk)
    if not can_edit(request.user, secret):
        raise PermissionDenied
    form = SecretForm(request.POST or None, instance=secret)
    if form.is_valid():
        secret = form.save(commit=False)
        if form.cleaned_data["value"].strip():
            secret.set_value(form.cleaned_data["value"])
        secret.save()
        write_log("UPDATE", user=request.user, secret=secret)
        messages.success(request, "Changes saved.")
        return back_to_vault(secret.workspace_id)
    return render(request, "secret_form.html", {
        "form": form, "title": f"Edit {secret.title}", "workspace": secret.workspace})


@login_required
@require_POST
def secret_delete(request, pk):
    secret = get_secret(request.user, pk)
    if not can_edit(request.user, secret):
        raise PermissionDenied
    write_log("DELETE", user=request.user, secret=secret)
    workspace_id = secret.workspace_id
    secret.delete()
    messages.success(request, "Secret deleted.")
    return back_to_vault(workspace_id)


@never_cache
@login_required
@require_POST
def secret_reveal(request, pk):
    secret = get_secret(request.user, pk)
    write_log("VIEW", user=request.user, secret=secret)
    return JsonResponse({"value": secret.get_value()})


@login_required
def workspace_create(request):
    form = WorkspaceForm(request.POST or None)
    if form.is_valid():
        workspace = form.save()
        WorkspaceMember.objects.create(
            workspace=workspace, user=request.user, role=WorkspaceMember.ADMIN)
        write_log("WORKSPACE_CREATE", user=request.user, workspace=workspace, detail=workspace.name)
        return back_to_vault(workspace.pk)
    return render(request, "form.html", {"form": form, "title": "New workspace", "submit": "Create workspace"})


@login_required
def workspace_members(request, workspace_id):
    workspace = get_workspace(request.user, workspace_id)
    admin = is_admin(request.user, workspace)
    form = InviteForm(request.POST or None)

    if request.method == "POST":
        if not admin:
            raise PermissionDenied
        if form.is_valid():
            email = form.cleaned_data["email"]
            role = form.cleaned_data["role"]
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                messages.error(request, "No account uses that e-mail yet.")
            elif WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
                messages.error(request, f"{user.username} is already a member.")
            else:
                WorkspaceMember.objects.create(workspace=workspace, user=user, role=role)
                write_log("MEMBER_ADD", user=request.user, workspace=workspace, detail=f"{user.username} as {role}")
                messages.success(request, f"{user.username} was added.")
            return redirect("workspace_members", workspace_id=workspace.pk)

    members = WorkspaceMember.objects.filter(workspace=workspace).select_related("user")
    return render(request, "members.html", {
        "workspace": workspace, "members": members, "form": form, "is_admin": admin})


@login_required
def audit(request):
    admin_of = Workspace.objects.filter(
        workspacemember__user=request.user, workspacemember__role=WorkspaceMember.ADMIN)
    logs = AuditLog.objects.filter(
        Q(user=request.user) | Q(workspace__in=admin_of)).select_related("user")[:100]
    return render(request, "audit.html", {"logs": logs})
