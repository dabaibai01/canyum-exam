"""题目图片上传：管理员上传后返回可直接访问的 URL。"""
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.deps import require_admin

router = APIRouter(prefix="/api/upload", tags=["上传"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.getenv("UPLOAD_DIR") or os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_SIZE = 8 * 1024 * 1024


def _detect_ext(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return ".gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    return None


@router.post("/image", dependencies=[Depends(require_admin)])
async def upload_image(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件为空")
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片不能超过 8MB")

    ext = _detect_ext(data)
    if not ext:
        raise HTTPException(status_code=400, detail="只支持 jpg、png、webp、gif 图片")

    filename = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(data)

    return {"url": f"/api/uploads/{filename}", "filename": filename}

