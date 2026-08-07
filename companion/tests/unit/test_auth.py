import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

from src.auth import require_user
from src.config import Config


def make_config() -> Config:
    return Config(
        graph_api_url="http://unused",
        graph_api_token="t",
        core_api_url="http://unused",
        core_api_token="t",
        companion_username="alice",
        companion_password="s3cret",
    )


def test_valid_credentials_are_accepted():
    verify = require_user(make_config())
    verify(credentials=HTTPBasicCredentials(username="alice", password="s3cret"))  # non solleva


def test_wrong_password_is_rejected():
    verify = require_user(make_config())
    with pytest.raises(HTTPException) as exc_info:
        verify(credentials=HTTPBasicCredentials(username="alice", password="wrong"))
    assert exc_info.value.status_code == 401


def test_wrong_username_is_rejected():
    verify = require_user(make_config())
    with pytest.raises(HTTPException) as exc_info:
        verify(credentials=HTTPBasicCredentials(username="mallory", password="s3cret"))
    assert exc_info.value.status_code == 401
