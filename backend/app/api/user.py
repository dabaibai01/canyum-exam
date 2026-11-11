from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.core.security import get_password_hash, is_legacy_hash, verify_password
from app.models.exam import ExamAttempt
from app.models.practice import UserAnswer, WrongQuestion
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("/list")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = db.query(User)
    if keyword:
        query = query.filter(
            (User.username.contains(keyword)) | (User.real_name.contains(keyword))
        )
    total = query.count()
    users = query.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "real_name": u.real_name,
            "phone": u.phone,
            "department": u.department,
            "position": u.position,
            "role": u.role,
            "avatar": u.avatar,
        })
    return {"total": total, "items": result}


@router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {
        "id": user.id,
        "username": user.username,
        "real_name": user.real_name,
        "phone": user.phone,
        "department": user.department,
        "position": user.position,
        "role": user.role,
    }


@router.post("/")
def create_user(
    data: dict,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    username = (data.get("username") or "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    password = (data.get("password") or "").strip()
    if not password:
        raise HTTPException(status_code=400, detail="请设置初始密码")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")

    user = User(
        username=username,
        password_hash=get_password_hash(password),
        real_name=data.get("real_name") or username,
        phone=data.get("phone"),
        department=data.get("department"),
        position=data.get("position"),
        role="admin" if data.get("role") == "admin" else "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "创建成功", "id": user.id}


@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: dict,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    for key in ["real_name", "phone", "department", "position", "role"]:
        if key in data:
            setattr(user, key, data[key])

    if data.get("password"):
        password = str(data["password"]).strip()
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="密码至少 6 位")
        user.password_hash = get_password_hash(password)

    db.commit()
    return {"message": "更新成功"}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="不能删除管理员账号")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录账号")

    # 一并清掉该学员的答题、错题、考试记录，避免留下孤儿数据
    db.query(UserAnswer).filter(UserAnswer.user_id == user.id).delete()
    db.query(WrongQuestion).filter(WrongQuestion.user_id == user.id).delete()
    db.query(ExamAttempt).filter(ExamAttempt.user_id == user.id).delete()
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}


@router.post("/change-password")
def change_password(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="参数不完整")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码不正确")

    current_user.password_hash = get_password_hash(new_password)
    db.commit()
    return {"message": "密码修改成功"}
