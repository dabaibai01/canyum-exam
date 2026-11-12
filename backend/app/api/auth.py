import re

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

    if user.status == "pending":
        raise HTTPException(status_code=403, detail="账号正在等待管理员审核，请审核通过后再登录")
    if user.status == "rejected":
        raise HTTPException(status_code=403, detail="注册申请未通过审核，请联系管理员")

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

@router.post("/register")
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    username = (user_in.username or "").strip()
    real_name = (user_in.real_name or "").strip()
    password = (user_in.password or "").strip()

    if len(username) < 3 or len(username) > 50:
        raise HTTPException(status_code=400, detail="用户名长度应为 3-50 个字符")
    if not re.fullmatch(r"[\w\u4e00-\u9fa5.-]+", username):
        raise HTTPException(status_code=400, detail="用户名只能包含字母、数字、下划线、中文、点或短横线")
    if not real_name:
        raise HTTPException(status_code=400, detail="请填写姓名")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")

    phone = (user_in.phone or "").strip() or None
    if phone and not re.fullmatch(r"1\d{10}", phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确，应为 11 位数字")

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在，请更换用户名")

    user = User(
        username=username,
        password_hash=get_password_hash(password),
        real_name=real_name,
        phone=phone,
        department=(user_in.department or "").strip() or None,
        position=(user_in.position or "").strip() or None,
        role="user",
        status="pending",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 自助注册不直接发 token，必须等管理员在后台审核通过后才能登录。
    return {
        "message": "注册申请已提交，请等待管理员审核通过后再登录",
        "id": user.id,
        "status": user.status,
    }
