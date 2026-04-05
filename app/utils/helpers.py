"""Utility helper functions."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import settings


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.

    Args:
        filename: Original filename

    Returns:
        Lowercase file extension without dot
    """
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def validate_video_file(file: UploadFile) -> None:
    """
    Validate uploaded video file.

    Args:
        file: Uploaded file object

    Raises:
        HTTPException: If file is invalid
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    extension = get_file_extension(file.filename)

    if extension not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format: .{extension}. "
            f"Allowed formats: {', '.join(settings.allowed_extensions)}",
        )


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename preserving the original extension.

    Args:
        original_filename: Original uploaded filename

    Returns:
        Unique filename with UUID prefix
    """
    extension = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}.{extension}"


def get_upload_path(filename: str) -> Path:
    """
    Get the full path for an uploaded file.

    Args:
        filename: Filename to use

    Returns:
        Full path in upload directory
    """
    return settings.upload_dir / filename


async def save_upload_file(file: UploadFile, destination: Path) -> None:
    """
    Save an uploaded file to disk.

    Args:
        file: Uploaded file object
        destination: Path to save file
    """
    content = await file.read()

    # Check file size
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {size_mb:.1f}MB. "
            f"Maximum allowed: {settings.max_file_size_mb}MB",
        )

    with open(destination, "wb") as f:
        f.write(content)
