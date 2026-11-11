"""站点设置：公开读取品牌信息，管理员修改名称、Logo、开发者和备案号。"""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.upload import UPLOAD_DIR, _detect_ext
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.site_setting import SiteSetting
from app.schemas.site_setting import SiteSettingsOut, SiteSettingsUpdate

router = APIRouter(prefix="/api/site", tags=["站点设置"])

DEFAULT_VALUES = {
    "site_name": "可以云码考试系统",
    "site_subtitle": "考试 · 刷题 · 组卷",
    "developer_name": "可以云码软件开发",
    "footer_text": "可以云码考试系统",
    "icp_no": "",
    "logo_url": "",
}

EDITABLE_KEYS = tuple(DEFAULT_VALUES.keys())
MAX_LOGO_SIZE = 2 * 1024 * 1024


def _read_values(db: Session) -> dict[str, str]:
    values = dict(DEFAULT_VALUES)
    rows = db.query(SiteSetting).filter(SiteSetting.key.in_(EDITABLE_KEYS)).all()
    for row in rows:
        values[row.key] = row.value or ""
    return values


@router.get("", response_model=SiteSettingsOut)
def get_site_settings(db: Session = Depends(get_db)):
    return _read_values(db)


@router.put("", response_model=SiteSettingsOut)
def update_site_settings(
    data: SiteSettingsUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    payload = data.model_dump(exclude_unset=True)
    if "site_name" in payload and not (payload["site_name"] or "").strip():
        raise HTTPException(status_code=400, detail="系统名称不能为空")

    for key, value in payload.items():
        if key not in EDITABLE_KEYS:
            continue
        cleaned = (value or "").strip() if isinstance(value, str) else value
        if key == "logo_url" and cleaned and not cleaned.startswith("/api/uploads/"):
            raise HTTPException(status_code=400, detail="Logo 地址不合法")
        row = db.query(SiteSetting).filter(SiteSetting.key == key).first()
        if row:
            row.value = cleaned or ""
        else:
            db.add(SiteSetting(key=key, value=cleaned or ""))

    db.commit()
    return _read_values(db)


@router.post("/logo")
async def upload_site_logo(
    file: UploadFile = File(...),
    _admin=Depends(require_admin),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件为空")
    if len(data) > MAX_LOGO_SIZE:
        raise HTTPException(status_code=400, detail="Logo 不能超过 2MB")

    ext = _detect_ext(data)
    if not ext:
        raise HTTPException(status_code=400, detail="只支持 jpg、png、webp、gif 图片")

    logo_dir = os.path.join(UPLOAD_DIR, "site")
    os.makedirs(logo_dir, exist_ok=True)
    filename = f"logo-{uuid.uuid4().hex}{ext}"
    with open(os.path.join(logo_dir, filename), "wb") as out:
        out.write(data)

    return {"logo_url": f"/api/uploads/site/{filename}", "filename": filename}
