from django.contrib.auth.models import AbstractUser
from django.db import models

from .crypto import decrypt, encrypt


class User(AbstractUser):
    email = models.EmailField(unique=True)


class Workspace(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    ROLES = [(ADMIN, "Admin"), (MEMBER, "Member")]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default=MEMBER)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["workspace", "user"], name="unique_member")]


class Secret(models.Model):
    TYPES = [
        ("PASSWORD", "Password"),
        ("API_KEY", "API key"),
        ("SSH_KEY", "SSH key"),
        ("CERTIFICATE", "Certificate"),
    ]

    secret_type = models.CharField(max_length=12, choices=TYPES, default="PASSWORD")
    title = models.CharField(max_length=150)
    username = models.CharField(max_length=150, blank=True)
    url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    encrypted_value = models.TextField(blank=True)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def set_value(self, plain):
        self.encrypted_value = encrypt(plain)

    def get_value(self):
        return decrypt(self.encrypted_value)


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    workspace = models.ForeignKey(Workspace, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=20)
    secret_title = models.CharField(max_length=150, blank=True)
    detail = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
