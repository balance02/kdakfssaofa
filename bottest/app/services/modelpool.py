from functools import lru_cache
from pathlib import Path

import yaml

CONFIG = Path(__file__).resolve().parents[2] / "config"


@lru_cache
def _models() -> dict:
    return yaml.safe_load((CONFIG / "models.yaml").read_text())


@lru_cache
def _pricing() -> dict:
    return yaml.safe_load((CONFIG / "pricing.yaml").read_text())


def resolve(mode: str) -> str:
    pool = _models()["mode_default"].get(mode, "cheap")
    return _models()[pool]


def cost(model: str, tokens_in: int, tokens_out: int) -> float:
    p = _pricing().get(model)
    if not p:
        return 0.0
    return tokens_in / 1_000_000 * p[0] + tokens_out / 1_000_000 * p[1]