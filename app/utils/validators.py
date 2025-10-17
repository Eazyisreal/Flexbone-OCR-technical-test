from app.utils.exceptions import ValidationError
from fastapi import UploadFile
from PIL import Image, ExifTags
import io
import bleach
from app.config import settings


async def validate_image(image: UploadFile) -> tuple[bytes, dict]:
    if not image:
        raise ValidationError("No image uploaded.")

    if image.content_type not in settings.supported_formats:
        raise ValidationError(
            f"Unsupported format: {image.content_type}. Supported: {', '.join(settings.supported_formats)}"
        )

    content = await image.read()
    if not content:
        raise ValidationError("Uploaded file is empty or unreadable.")

    # ✅ Check file size
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise ValidationError("File exceeds size limit.")

    try:
        image_stream = io.BytesIO(content)
        with Image.open(image_stream) as img:
            img.verify() 
            img = Image.open(io.BytesIO(content))
            metadata = {
                "format": img.format,
                "size": img.size,
                "mode": img.mode,
                "exif": {
                    ExifTags.TAGS.get(k, k): v for k, v in (img.getexif() or {}).items()
                } if hasattr(img, "getexif") else {}
            }
    except Exception as e:
        raise ValidationError(f"Invalid or corrupted image: {str(e)}")

    return content, metadata


def preprocess_text(text: str) -> str:
    """Cleans up and sanitizes extracted text"""
    text = text.strip().replace("\n", " ")
    return bleach.clean(text)
