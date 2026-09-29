from .models import AuditLog


def write_log(action, user=None, secret=None, workspace=None, detail=""):
    if user is not None and not user.is_authenticated:
        user = None
    if secret is not None and workspace is None:
        workspace = secret.workspace
    AuditLog.objects.create(
        user=user,
        workspace=workspace,
        action=action,
        secret_title=secret.title if secret else "",
        detail=detail,
    )
