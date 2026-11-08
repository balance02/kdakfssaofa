import hashlib
import hmac

from app.config import get_settings
from app.services.crypto import verify_signature


def test_signature_roundtrip(monkeypatch):
    monkeypatch.setenv("CRYPTO_PAY_TOKEN", "tok")
    get_settings.cache_clear()
    body = b'{"update_type":"invoice_paid"}'
    secret = hashlib.sha256(b"tok").digest()
    sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
    assert verify_signature(body, sig)
    assert not verify_signature(body, "deadbeef")