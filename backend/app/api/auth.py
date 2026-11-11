import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_password_hash,
    is_legacy_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.user import UserLogin, UserRegister, Token, UserOut

router = APIRouter(prefix="/api/auth", tags=["认证"])

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 老数据是无盐 SHA256，登录成功时顺手升级为 PBKDF2 加盐存储
    if is_legacy_hash(user.password_hash):
        user.password_hash = get_password_hash(user_in.password)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user)
    }

@router.post("/register", response_model=Token)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # 正式环境默认关闭自助注册，学员账号由管理员在后台创建
    if os.getenv("ALLOW_REGISTER") != "1":
        raise HTTPException(status_code=403, detail="系统未开放自助注册，请联系管理员开通账号")

    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        real_name=user_in.real_name,
        phone=user_in.phone,
        department=user_in.department,
        position=user_in.position,
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user)
    }
