import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, exam, media, notice, practice, question, site, stats, upload, user
from app.api.upload import UPLOAD_DIR
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.site_setting import SiteSetting
from app.models.user import User

# 建表（已有表不会被改动；新增字段请在 scripts 里显式迁移）
Base.metadata.create_all(bind=engine)


def bootstrap_admin():
    """全新库只放一个管理员账号，不再写入测试分类/测试题。"""
    db = SessionLocal()
    try:
        if not db.query(User).first():
            db.add(User(
                username=os.getenv("ADMIN_USERNAME", "admin"),
                password_hash=get_password_hash(os.getenv("ADMIN_PASSWORD", "admin123")),
                real_name="管理员",
                role="admin",
                department="机关",
            ))
            db.commit()
            print("[bootstrap] 已创建初始管理员账号，请尽快在后台修改密码")
    finally:
        db.close()


bootstrap_admin()

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(question.router)
app.include_router(practice.router)
app.include_router(exam.router)
app.include_router(media.router)
app.include_router(user.router)
app.include_router(stats.router)
app.include_router(notice.router)
app.include_router(upload.router)
app.include_router(site.router)

# 题目图片等上传文件，通过 /api/uploads/... 访问（Vite 与 Nginx 都只代理 /api）
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running"}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "服务正常运行"}
