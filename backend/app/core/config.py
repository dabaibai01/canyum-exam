import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    if raw.strip():
        return [item.strip() for item in raw.split(",") if item.strip()]
    # 本地开发默认放行两个 Vite 端口
    return [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]


class Settings:
    APP_NAME: str = "可以云码考试系统"
    APP_VERSION: str = "1.0.0"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "canyum-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "720"))

    CORS_ORIGINS: list[str] = _cors_origins()


settings = Settings()
