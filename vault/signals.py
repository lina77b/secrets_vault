from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from .audit import write_log


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    write_log("LOGIN", user=user)


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    write_log("LOGOUT", user=user)


@receiver(user_login_failed)
def on_login_failed(sender, credentials, **kwargs):
    write_log("LOGIN_FAILED", detail=f"username={credentials.get('username', '')}")
