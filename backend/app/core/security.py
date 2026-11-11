import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings

PBKDF2_ITERATIONS = 120_000
LEGACY_SHA256_LEN = 64


def _pbkdf2_hash(password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2${iterations}${salt.hex()}${digest.hex()}"


def get_password_hash(password: str) -> str:
    """新密码统一用 PBKDF2-SHA256 加盐存储"""
    salt = os.urandom(16)
    return _pbkdf2_hash(password, salt)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """兼容历史 SHA256 明文摘要，登录成功后由调用方决定是否升级"""
    if not hashed_password:
        return False
    if hashed_password.startswith("pbkdf2$"):
        try:
            _, iterations, salt_hex, digest_hex = hashed_password.split("$", 3)
            candidate = _pbkdf2_hash(plain_password, bytes.fromhex(salt_hex), int(iterations))
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(candidate, hashed_password)
    # 旧数据：无盐 sha256
    return hmac.compare_digest(
        hashlib.sha256(plain_password.encode()).hexdigest(),
        hashed_password,
    )


def is_legacy_hash(hashed_password: str) -> bool:
    return bool(hashed_password) and not hashed_password.startswith("pbkdf2$")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
