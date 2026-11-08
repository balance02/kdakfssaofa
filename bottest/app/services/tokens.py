def estimate(text: str) -> int:
    """Грубая оценка токенов: ~3 символа на токен для ru/en смеси."""
    return max(1, len(text) // 3)


def estimate_messages(messages: list[dict]) -> int:
    return sum(estimate(m["content"]) + 4 for m in messages)