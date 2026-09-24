"""图片上传服务，MVP 阶段支持本地存储和阿里云 OSS"""
import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from core.config import settings

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB
LOCAL_UPLOAD_DIR = Path("uploads")


async def upload_image(file: UploadFile) -> str:
    """上传图片，返回可访问的URL"""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="只支持 JPG、PNG、WEBP 格式图片")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"

    # 有 OSS 配置就上传到 OSS，否则存本地（开发阶段）
    if settings.OSS_ACCESS_KEY_ID:
        return await _upload_oss(content, filename, file.content_type)
    else:
        return _save_local(content, filename)


def _save_local(content: bytes, filename: str) -> str:
    LOCAL_UPLOAD_DIR.mkdir(exist_ok=True)
    path = LOCAL_UPLOAD_DIR / filename
    path.write_bytes(content)
    return f"/uploads/{filename}"


async def _upload_oss(content: bytes, filename: str, content_type: str) -> str:
    import oss2
    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
    key = f"homework/{filename}"
    bucket.put_object(key, content, headers={"Content-Type": content_type})
    domain = settings.OSS_DOMAIN or f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT.replace('https://', '')}"
    return f"{domain}/{key}"
