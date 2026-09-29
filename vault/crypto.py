import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _key():
    return base64.urlsafe_b64decode(os.environ["ENCRYPTION_KEY"])


def encrypt(text):
    nonce = os.urandom(12)
    data = AESGCM(_key()).encrypt(nonce, text.encode(), None)
    return base64.urlsafe_b64encode(nonce + data).decode()


def decrypt(token):
    raw = base64.urlsafe_b64decode(token)
    return AESGCM(_key()).decrypt(raw[:12], raw[12:], None).decode()
