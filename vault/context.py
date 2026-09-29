from .models import Workspace


def workspaces(request):
    if not request.user.is_authenticated:
        return {}
    return {"my_workspaces": Workspace.objects.filter(workspacemember__user=request.user)}
