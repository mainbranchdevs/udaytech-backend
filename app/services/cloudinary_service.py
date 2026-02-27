import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


async def upload_image(file: UploadFile, folder: str = "udayatech") -> str:
    contents = await file.read()
    result = cloudinary.uploader.upload(contents, folder=folder)
    return result["secure_url"]
