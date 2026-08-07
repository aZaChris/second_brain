from src.auth import is_authorized


def test_authorized_user_is_allowed():
    assert is_authorized(123, frozenset({123, 456})) is True


def test_unknown_user_is_blocked():
    assert is_authorized(999, frozenset({123, 456})) is False
