from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password/", views.PasswordChange.as_view(), name="password_change"),
    path("secrets/add/", views.secret_create, name="secret_create"),
    path("secrets/<int:pk>/edit/", views.secret_edit, name="secret_edit"),
    path("secrets/<int:pk>/delete/", views.secret_delete, name="secret_delete"),
    path("secrets/<int:pk>/reveal/", views.secret_reveal, name="secret_reveal"),
    path("workspaces/new/", views.workspace_create, name="workspace_create"),
    path("workspaces/<int:workspace_id>/", views.dashboard, name="workspace"),
    path("workspaces/<int:workspace_id>/secrets/add/", views.secret_create, name="workspace_secret_create"),
    path("workspaces/<int:workspace_id>/members/", views.workspace_members, name="workspace_members"),
    path("audit/", views.audit, name="audit"),
]
