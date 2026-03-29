from app.auth.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_and_verify_password():
    password = "super-secret-123"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("bad-password", password_hash)


def test_create_and_decode_access_token():
    token, _ = create_access_token(user_id=99)
    payload = decode_access_token(token)

    assert payload["sub"] == "99"
    assert "exp" in payload
