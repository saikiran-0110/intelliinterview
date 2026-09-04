import pytest

from app.email_types import normalize_flexible_email
from app.schemas import utc_now_iso
from app.config import Settings


def test_normalize_flexible_email_accepts_dev_domains():
    assert normalize_flexible_email("  User@Test.COM ") == "user@test.com"
    assert normalize_flexible_email("a@localhost") == "a@localhost"
    assert normalize_flexible_email("demo@example") == "demo@example"


def test_normalize_flexible_email_rejects_invalid():
    with pytest.raises(ValueError, match="valid email"):
        normalize_flexible_email("not-an-email")
    with pytest.raises(ValueError, match="valid email"):
        normalize_flexible_email("missing-domain@")
    with pytest.raises(ValueError, match="valid email"):
        normalize_flexible_email("has space@test.com")


def test_utc_now_iso_is_timezone_aware():
    stamp = utc_now_iso()
    assert "T" in stamp
    assert stamp.endswith("+00:00") or stamp.endswith("Z") or "+" in stamp[10:]


def test_cors_origin_list_splits_and_strips():
    settings = Settings()
    settings.cors_origins = "http://localhost:5173, http://localhost:3000, "
    assert settings.cors_origin_list == ["http://localhost:5173", "http://localhost:3000"]
