import hashlib
import hmac
import json
import uuid

import httpx

from app.config import get_settings


def _headers() -> dict:
    return {"Crypto-Pay-API-Token": get_settings().crypto_pay_token}


async def create_invoice(user_id: int, amount: float, days: int) -> tuple[str, str]:
    payload = {
        "asset": "USDT",
        "amount": f"{amount:.2f}",
        "currency_type": "fiat",
        "fiat": "USD",
        "expires_in": 3600,
        "description": f"Uncensored AI — {days} days",
        "payload": json.dumps({"user_id": user_id, "days": days, "nonce": uuid.uuid4().hex}),
    }
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{get_settings().crypto_base}/createInvoice", json=payload,
                         headers=_headers())
        if r.status_code != 200:
            print("CRYPTO ERROR", r.status_code, r.text)
        r.raise_for_status()
        res = r.json()
    if not res.get("ok"):
        raise RuntimeError(res)
    inv = res["result"]
    return str(inv["invoice_id"]), inv["bot_invoice_url"]


async def get_invoice(invoice_id: str) -> dict | None:
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{get_settings().crypto_base}/getInvoices",
                         json={"invoice_ids": invoice_id}, headers=_headers())
        r.raise_for_status()
        res = r.json()
    items = res.get("result", {}).get("items", [])
    return items[0] if items else None


def verify_signature(raw_body: bytes, signature: str) -> bool:
    secret = hashlib.sha256(get_settings().crypto_pay_token.encode()).digest()
    expected = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")