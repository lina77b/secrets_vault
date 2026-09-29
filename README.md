# SecVault

[![Tests](https://github.com/lina77b/secrets_vault/actions/workflows/tests.yml/badge.svg)](https://github.com/lina77b/secvault/actions/workflows/tests.yml)

SecVault is a small web app for keeping passwords, API keys, SSH keys and certificates in one place instead of scattered across chats and sticky notes. Everything you save is encrypted before it touches the database.

You get a personal vault that only you can see. You can also create workspaces for a team, invite people who already have an account, and share secrets there.

Built with Django, PostgreSQL and Docker.

## What you can do

- Create an account and sign in
- Store four kinds of secrets: passwords, API keys, SSH keys and certificates
- Show or copy a secret only when you need it (it stays hidden on the page otherwise)
- Generate a strong password while adding a secret
- Create workspaces and add teammates as **members** or **admins**
- See who did what in the audit log

In a workspace, members can view and add secrets. Admins can also edit and delete secrets and manage the member list.

## Running it

You need Docker. Then:

1. Copy the example settings:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and replace the three `change-me` values. You can generate good ones like this:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
   ```

   Use the first for `DJANGO_SECRET_KEY` and the second for `ENCRYPTION_KEY`. Pick any long password for `POSTGRES_PASSWORD`.

3. Start it:

   ```bash
   docker compose up --build
   ```

4. Open http://localhost:8000 and create an account.

**Keep your `ENCRYPTION_KEY` safe and do not change it.** If you lose it, the saved secrets cannot be read anymore, so be careful.

### Without Docker

This uses a local SQLite file instead of PostgreSQL:

```bash
pip install -r requirements.txt
export DJANGO_SECRET_KEY=put_anything_you_want DEBUG=1 ENCRYPTION_KEY=<a key made with the command above>
python manage.py migrate
python manage.py runserver
```

## How it works

When you save a secret, the app encrypts it with AES-256-GCM using your `ENCRYPTION_KEY`, and only the encrypted text goes into the database. It is decrypted when you press Show or Copy, and each of those actions is written to the audit log.

Every page checks who is asking. A secret is only found if it is yours or belongs to a workspace you are part of, otherwise the app answers "not found".

Passwords need at least 12 characters, and sessions expire after 30 minutes of inactivity.

## Project layout

```
config/       Django settings and the root URL file
vault/        The app itself
  models.py     User, Workspace, Secret, AuditLog
  views.py      All the pages
  forms.py      Forms
  crypto.py     Encrypt and decrypt
  audit.py      Writes audit log entries
  tests.py      Automated tests
templates/    HTML pages
static/       CSS and JavaScript
```

## Tests

```bash
DJANGO_SECRET_KEY=test python manage.py test
```

## Good to know

This is a learning project, so a few things are left out :

- It runs over plain HTTP. For real use, put it behind an HTTPS reverse proxy such as Caddy or nginx.
- There is no two-factor login and no limit on failed login attempts.
- There is no key rotation. Changing `ENCRYPTION_KEY` makes old secrets unreadable.
- Audit log entries are protected by the app, not by the database.

## License

MIT. See the [LICENSE](LICENSE) file.
