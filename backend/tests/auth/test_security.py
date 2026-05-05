"""Unit tests for password hashing and JWT helpers."""

from __future__ import annotations

from datetime import timedelta

import jwt
import pytest

from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.config import settings


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("secret-pw-1234")
        assert hashed != "secret-pw-1234"
        assert hashed.startswith("$2")  # bcrypt prefix

    def test_verify_accepts_correct_password(self):
        hashed = hash_password("secret-pw-1234")
        assert verify_password("secret-pw-1234", hashed) is True

    def test_verify_rejects_wrong_password(self):
        hashed = hash_password("secret-pw-1234")
        assert verify_password("WRONG", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        # bcrypt salts each hash, so the same input must produce different hashes
        assert hash_password("same") != hash_password("same")

    def test_verify_returns_false_on_malformed_hash(self):
        # bcrypt raises ValueError on a hash that isn't a valid bcrypt string;
        # verify_password must swallow it and return False.
        assert verify_password("anything", "not-a-valid-bcrypt-hash") is False


class TestJWT:
    def test_round_trip_subject(self):
        token = create_access_token(subject=42)
        payload = decode_access_token(token)
        assert payload["sub"] == "42"

    def test_token_contains_expiry(self):
        token = create_access_token(subject=1)
        payload = decode_access_token(token)
        assert "exp" in payload

    def test_extra_claims_are_included(self):
        token = create_access_token(subject=1, extra_claims={"role": "admin"})
        payload = decode_access_token(token)
        assert payload["role"] == "admin"

    def test_expired_token_raises(self):
        token = create_access_token(subject=1, expires_delta=timedelta(seconds=-10))
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_tampered_signature_raises(self):
        token = create_access_token(subject=1)
        # Mangle the signature segment
        head, body, _sig = token.split(".")
        tampered = f"{head}.{body}.invalid_signature_segment"
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token(tampered)

    def test_token_signed_with_wrong_key_raises(self):
        # Sign with a different key, then try to decode with the app key
        bad_token = jwt.encode({"sub": "1"}, "different-key", algorithm=settings.ALGORITHM)
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token(bad_token)
