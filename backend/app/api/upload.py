"""文件上传：题目图片、教学视频、书籍文档。

图片保持原有的小文件上传逻辑；视频和文档使用分块落盘，避免把大文件整体读入内存。
"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.deps import require_admin

router = APIRouter(prefix="/api/upload", tags=["上传"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.getenv("UPLOAD_DIR") or os.path.join(BASE_DIR, "uploads")
VIDEO_DIR = os.path.join(UPLOAD_DIR, "videos")
BOOK_DIR = os.path.join(UPLOAD_DIR, "books")
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(BOOK_DIR, exist_ok=True)

MAX_IMAGE_SIZE = 8 * 1024 * 1024
MAX_VIDEO_SIZE = 512 * 1024 * 1024
MAX_BOOK_SIZE = 100 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024

VIDEO_EXTS = {".mp4", ".m4v", ".webm", ".ogg", ".ogv"}
BOOK_EXTS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".epub"}

VIDEO_MIME = {
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".webm": "video/webm",
    ".ogg": "video/ogg",
    ".ogv": "video/ogg",
}


def _detect_image_ext(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return ".gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    return None


# 兼容站点 Logo 上传模块原有的导入名。
_detect_ext = _detect_image_ext


def _video_magic_ok(ext: str, head: bytes) -> bool:
    if ext in (".mp4", ".m4v"):
        return len(head) >= 12 and head[4:8] == b"ftyp"
    if ext == ".webm":
        return head.startswith(b"\x1aE\xdf\xa3")
    if ext in (".ogg", ".ogv"):
        return head.startswith(b"OggS")
    return False


def _book_magic_ok(ext: str, head: bytes) -> bool:
    if ext == ".pdf":
        return head.startswith(b"%PDF")
    if ext in (".doc", ".ppt", ".xls"):
        return head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    if ext in (".docx", ".pptx", ".xlsx", ".epub"):
        return head.startswith(b"PK\x03\x04") or head.startswith(b"PK\x05\x06") or head.startswith(b"PK\x07\x08")
    if ext == ".txt":
        return True
    return False


def _ext_of(filename: str | None) -> str:
    return Path(filename or "").suffix.lower()


def _local_path(url: str | None) -> Path | None:
    """把 /api/uploads/... 地址解析为 uploads 目录内的真实文件。"""
    if not url or not url.startswith("/api/uploads/"):
        return None
    rel = url[len("/api/uploads/"):].lstrip("/")
    if not rel or ".." in rel.split("/"):
        return None
    root = Path(UPLOAD_DIR).resolve()
    target = (root / rel).resolve()
    if root != target and root not in target.parents:
        return None
    return target if target.is_file() else None


def resolve_local_file(url: str | None) -> Path | None:
    return _local_path(url)


def delete_local_file(url: str | None) -> None:
    path = _local_path(url)
    if path:
        try:
            path.unlink()
        except OSError:
            pass


async def _save_large_file(
    file: UploadFile,
    target_dir: str,
    allowed_exts: set[str],
    max_size: int,
    kind: str,
) -> dict:
    ext = _ext_of(file.filename)
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"不支持的{kind}格式：{ext or '未知'}")

    head = await file.read(24)
    if not head:
        raise HTTPException(status_code=400, detail="文件为空")

    ok = _video_magic_ok(ext, head) if kind == "视频" else _book_magic_ok(ext, head)
    if not ok:
        raise HTTPException(status_code=400, detail=f"文件内容与{kind}格式不匹配，请检查文件是否损坏或改过后缀")

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(target_dir, filename)
    temp = dest + ".part"
    size = len(head)
    try:
        with open(temp, "wb") as out:
            out.write(head)
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_size:
                    raise HTTPException(status_code=413, detail=f"{kind}不能超过 {max_size // (1024 * 1024)}MB")
                out.write(chunk)
        os.replace(temp, dest)
    except HTTPException:
        try:
            os.remove(temp)
        except OSError:
            pass
        raise
    except Exception:
        try:
            os.remove(temp)
        except OSError:
            pass
        raise

    subdir = os.path.basename(target_dir)
    return {
        "url": f"/api/uploads/{subdir}/{filename}",
        "filename": filename,
        "original_name": file.filename or filename,
        "size": size,
        "content_type": VIDEO_MIME.get(ext) if kind == "视频" else file.content_type,
    }


@router.post("/image", dependencies=[Depends(require_admin)])
async def upload_image(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件为空")
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片不能超过 8MB")

    ext = _detect_image_ext(data)
    if not ext:
        raise HTTPException(status_code=400, detail="只支持 jpg、png、webp、gif 图片")

    filename = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(data)

    return {"url": f"/api/uploads/{filename}", "filename": filename}


@router.post("/video", dependencies=[Depends(require_admin)])
async def upload_video(file: UploadFile = File(...)):
    return await _save_large_file(file, VIDEO_DIR, VIDEO_EXTS, MAX_VIDEO_SIZE, "视频")


@router.post("/book", dependencies=[Depends(require_admin)])
async def upload_book(file: UploadFile = File(...)):
    return await _save_large_file(file, BOOK_DIR, BOOK_EXTS, MAX_BOOK_SIZE, "书籍文档")
