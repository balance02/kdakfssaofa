import json
from pathlib import Path

LOCALES = Path(__file__).resolve().parents[1] / "locales"


def test_catalogs_match():
    ru = json.loads((LOCALES / "ru.json").read_text(encoding="utf-8"))
    en = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    assert set(ru) == set(en)


def test_placeholders_match():
    ru = json.loads((LOCALES / "ru.json").read_text(encoding="utf-8"))
    en = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    for key, value in ru.items():
        assert value.count("{") == en[key].count("{"), key