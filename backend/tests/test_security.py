from uuid import uuid4

import jwt

from app.config import settings
from app.models import UserRole
from app.services.security import create_access_token, hash_password, verify_password


def test_hash_and_verify_password():
    hashed = hash_password("password123")
    assert hashed != "password123"
    assert verify_password("password123", hashed)
    assert not verify_password("wrong-password", hashed)


def test_create_access_token_contains_claims():
    user_id = uuid4()
    token = create_access_token(user_id, "recruiter@example.com", UserRole.RECRUITER)
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == str(user_id)
    assert payload["email"] == "recruiter@example.com"
    assert payload["role"] == "RECRUITER"
    assert "exp" in payload
