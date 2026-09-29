import base64
import os

os.environ.setdefault("ENCRYPTION_KEY", base64.urlsafe_b64encode(b"k" * 32).decode())

from cryptography.exceptions import InvalidTag
from django.test import TestCase

from .crypto import decrypt, encrypt
from .models import AuditLog, Secret, User, Workspace, WorkspaceMember

PASSWORD = "Tr0ub4dor&3-horse-battery"


class VaultTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("admin", "admin@x.io", PASSWORD)
        cls.member = User.objects.create_user("member", "member@x.io", PASSWORD)
        cls.stranger = User.objects.create_user("stranger", "stranger@x.io", PASSWORD)

        cls.team = Workspace.objects.create(name="Team")
        WorkspaceMember.objects.create(workspace=cls.team, user=cls.admin, role="ADMIN")
        WorkspaceMember.objects.create(workspace=cls.team, user=cls.member, role="MEMBER")

        cls.shared = cls.make_secret(workspace=cls.team)
        cls.private = cls.make_secret(owner=cls.admin)

    @staticmethod
    def make_secret(**kwargs):
        secret = Secret(title="Example", **kwargs)
        secret.set_value("hunter2-value")
        secret.save()
        return secret


class EncryptionTests(VaultTestCase):
    def test_round_trip(self):
        self.assertEqual(decrypt(encrypt("hello")), "hello")

    def test_value_is_not_stored_in_plain_text(self):
        self.assertNotIn("hunter2", self.shared.encrypted_value)
        self.assertEqual(self.shared.get_value(), "hunter2-value")

    def test_tampered_value_is_rejected(self):
        token = base64.urlsafe_b64decode(encrypt("hello"))
        broken = base64.urlsafe_b64encode(token[:-1] + bytes([token[-1] ^ 1])).decode()
        with self.assertRaises(InvalidTag):
            decrypt(broken)


class AccountTests(VaultTestCase):
    def test_register_logs_the_user_in(self):
        response = self.client.post("/register/", {
            "username": "new", "email": "new@x.io",
            "password1": PASSWORD, "password2": PASSWORD})
        self.assertRedirects(response, "/")
        self.assertTrue(User.objects.filter(username="new").exists())

    def test_short_password_is_rejected(self):
        response = self.client.post("/register/", {
            "username": "new", "email": "new@x.io",
            "password1": "Short1!", "password2": "Short1!"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="new").exists())

    def test_login_and_failed_login_are_logged(self):
        self.client.post("/login/", {"username": "admin", "password": "wrong"})
        self.assertTrue(AuditLog.objects.filter(action="LOGIN_FAILED").exists())
        self.client.post("/login/", {"username": "admin", "password": PASSWORD})
        self.assertTrue(AuditLog.objects.filter(action="LOGIN", user=self.admin).exists())

    def test_pages_need_a_login(self):
        for url in ("/", "/audit/", f"/workspaces/{self.team.pk}/"):
            self.assertEqual(self.client.get(url).status_code, 302)


class AccessTests(VaultTestCase):
    def test_stranger_cannot_open_workspace_or_its_secrets(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(f"/workspaces/{self.team.pk}/").status_code, 404)
        self.assertEqual(self.client.post(f"/secrets/{self.shared.pk}/reveal/").status_code, 404)

    def test_personal_secret_is_private(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(f"/secrets/{self.private.pk}/reveal/").status_code, 404)

    def test_member_can_read_but_not_change_shared_secret(self):
        self.client.force_login(self.member)
        response = self.client.post(f"/secrets/{self.shared.pk}/reveal/")
        self.assertEqual(response.json()["value"], "hunter2-value")
        self.assertEqual(self.client.get(f"/secrets/{self.shared.pk}/edit/").status_code, 403)
        self.assertEqual(self.client.post(f"/secrets/{self.shared.pk}/delete/").status_code, 403)

    def test_admin_can_delete_shared_secret(self):
        self.client.force_login(self.admin)
        self.client.post(f"/secrets/{self.shared.pk}/delete/")
        self.assertFalse(Secret.objects.filter(pk=self.shared.pk).exists())

    def test_reveal_needs_post(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(f"/secrets/{self.shared.pk}/reveal/").status_code, 405)

    def test_only_admins_add_members(self):
        url = f"/workspaces/{self.team.pk}/members/"
        data = {"email": "stranger@x.io", "role": "MEMBER"}
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(url, data).status_code, 403)
        self.client.force_login(self.admin)
        self.client.post(url, data)
        self.assertTrue(WorkspaceMember.objects.filter(user=self.stranger).exists())


class SecretFormTests(VaultTestCase):
    def test_create_personal_secret(self):
        self.client.force_login(self.member)
        self.client.post("/secrets/add/", {
            "secret_type": "API_KEY", "title": "Stripe", "value": "sk_test_123"})
        secret = Secret.objects.get(title="Stripe")
        self.assertEqual(secret.owner, self.member)
        self.assertEqual(secret.get_value(), "sk_test_123")

    def test_value_is_required_when_creating(self):
        self.client.force_login(self.member)
        response = self.client.post("/secrets/add/", {"secret_type": "PASSWORD", "title": "Empty", "value": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Secret.objects.filter(title="Empty").exists())

    def test_blank_value_keeps_old_one_when_editing(self):
        self.client.force_login(self.admin)
        self.client.post(f"/secrets/{self.private.pk}/edit/", {
            "secret_type": "PASSWORD", "title": "Renamed", "value": ""})
        self.private.refresh_from_db()
        self.assertEqual(self.private.title, "Renamed")
        self.assertEqual(self.private.get_value(), "hunter2-value")


class AuditTests(VaultTestCase):
    def test_reveal_is_logged_with_workspace(self):
        self.client.force_login(self.member)
        self.client.post(f"/secrets/{self.shared.pk}/reveal/")
        log = AuditLog.objects.get(action="VIEW")
        self.assertEqual((log.user, log.workspace), (self.member, self.team))

    def test_log_survives_secret_deletion(self):
        self.client.force_login(self.admin)
        self.client.post(f"/secrets/{self.shared.pk}/delete/")
        self.assertTrue(AuditLog.objects.filter(action="DELETE", secret_title="Example").exists())

    def test_members_do_not_see_other_peoples_workspace_activity(self):
        self.client.force_login(self.admin)
        self.client.post(f"/secrets/{self.shared.pk}/reveal/")
        self.client.force_login(self.member)
        self.assertNotContains(self.client.get("/audit/"), "<td>admin</td>")
