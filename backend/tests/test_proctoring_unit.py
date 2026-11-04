import json

from app.services import proctoring as proctoring_module
from app.services.proctoring import check_frame


class _FakeResponse:
    def __init__(self, content: dict):
        self._content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": json.dumps(self._content)}}]}


class _FakeErrorResponse:
    def raise_for_status(self):
        raise proctoring_module.httpx.HTTPStatusError("boom", request=None, response=self)

    status_code = 500
    text = "server error"


def test_no_api_key_fails_open():
    # conftest.py sets settings.openai_api_key = "" for the whole suite.
    result = check_frame(b"fake-jpeg-bytes")
    assert result == {"violation": False, "kind": None, "detail": ""}


def test_violation_parsed_from_model_response(monkeypatch):
    monkeypatch.setattr(proctoring_module.settings, "openai_api_key", "test-key")
    fake_payload = {"violation": True, "kind": "PROHIBITED_OBJECT", "detail": "A phone is visible on the desk."}
    monkeypatch.setattr(proctoring_module.httpx, "post", lambda *args, **kwargs: _FakeResponse(fake_payload))

    result = check_frame(b"fake-jpeg-bytes")

    assert result["violation"] is True
    assert result["kind"] == "PROHIBITED_OBJECT"
    assert result["detail"] == "A phone is visible on the desk."


def test_no_violation_response_passes_through(monkeypatch):
    monkeypatch.setattr(proctoring_module.settings, "openai_api_key", "test-key")
    fake_payload = {"violation": False, "kind": None, "detail": ""}
    monkeypatch.setattr(proctoring_module.httpx, "post", lambda *args, **kwargs: _FakeResponse(fake_payload))

    result = check_frame(b"fake-jpeg-bytes")

    assert result == {"violation": False, "kind": None, "detail": ""}


def test_unknown_kind_in_response_fails_open(monkeypatch):
    monkeypatch.setattr(proctoring_module.settings, "openai_api_key", "test-key")
    # A model response naming a kind outside the fixed enum must not be trusted verbatim.
    fake_payload = {"violation": True, "kind": "SUSPICIOUS_VIBES", "detail": "something"}
    monkeypatch.setattr(proctoring_module.httpx, "post", lambda *args, **kwargs: _FakeResponse(fake_payload))

    result = check_frame(b"fake-jpeg-bytes")

    assert result == {"violation": False, "kind": None, "detail": ""}


def test_http_error_fails_open(monkeypatch):
    monkeypatch.setattr(proctoring_module.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(proctoring_module.httpx, "post", lambda *args, **kwargs: _FakeErrorResponse())

    result = check_frame(b"fake-jpeg-bytes")

    assert result == {"violation": False, "kind": None, "detail": ""}


def test_unparsable_json_fails_open(monkeypatch):
    monkeypatch.setattr(proctoring_module.settings, "openai_api_key", "test-key")

    class _BadJsonResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "not json"}}]}

    monkeypatch.setattr(proctoring_module.httpx, "post", lambda *args, **kwargs: _BadJsonResponse())

    result = check_frame(b"fake-jpeg-bytes")

    assert result == {"violation": False, "kind": None, "detail": ""}
