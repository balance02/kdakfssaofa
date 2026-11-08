import json
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parents[2] / "locales"
SUPPORTED = ("ru", "en")
_cache: dict[str, dict[str, str]] = {}


def _load(lang: str) -> dict[str, str]:
    if lang not in _cache:
        _cache[lang] = json.loads((LOCALES_DIR / f"{lang}.json").read_text(encoding="utf-8"))
    return _cache[lang]


def resolve_lang(code: str | None) -> str:
    if not code:
        return "ru"
    return "ru" if code[:2] in ("ru", "uk", "be", "kk") else "en"


def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in SUPPORTED else "ru"
    text = _load(lang).get(key) or _load("ru").get(key) or key
    return text.format(**kwargs) if kwargs else text