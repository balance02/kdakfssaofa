from app.services.tokens import estimate, estimate_messages


def test_estimate_positive():
    assert estimate("") == 1
    assert estimate("a" * 30) == 10


def test_estimate_messages():
    assert estimate_messages([{"content": "a" * 30}]) == 14