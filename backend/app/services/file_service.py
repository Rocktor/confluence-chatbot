import os
import uuid
import aiofiles
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import io

UPLOAD_DIR = Path("/app/uploads")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_DOC_TYPES = {"application/pdf", "text/plain", "text/markdown",
                     "application/msword",
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
                     "application/vnd.ms-excel",                                           # .xls
                     }
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

# Magic bytes for file type validation
MAGIC_BYTES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
    b'RIFF': 'image/webp',  # WebP starts with RIFF
    b'%PDF': 'application/pdf',
    b'PK\x03\x04': 'zip_based',  # DOCX and XLSX both start with PK (ZIP format)
}

# ZIP-based Office formats (all start with PK\x03\x04)
ZIP_BASED_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",         # .xlsx
}

# Safe file extensions
SAFE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt', '.md',
                   '.doc', '.docx', '.xlsx', '.xls'}


class FileService:
    def __init__(self):
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def _validate_magic_bytes(self, content: bytes, claimed_type: str) -> bool:
        """Validate file content matches claimed type using magic bytes."""
        for magic, file_type in MAGIC_BYTES.items():
            if content.startswith(magic):
                # For WebP, need additional check
                if magic == b'RIFF' and len(content) > 12:
                    if content[8:12] == b'WEBP':
                        return claimed_type == 'image/webp'
                    return False
                # ZIP-based formats (DOCX, XLSX) all start with PK
                if file_type == 'zip_based':
                    return claimed_type in ZIP_BASED_TYPES
                return claimed_type == file_type or (
                    file_type.startswith('image/') and claimed_type.startswith('image/')
                )
        # Allow text files without magic bytes
        if claimed_type in {'text/plain', 'text/markdown'}:
            try:
                content[:1000].decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False
        return False

    def _sanitize_extension(self, filename: str) -> str:
        """Get safe file extension."""
        ext = Path(filename or "file").suffix.lower()
        if ext not in SAFE_EXTENSIONS:
            ext = '.bin'
        return ext

    async def upload_file(self, file: UploadFile, user_id: int) -> dict:
        """Upload a single file and return its URL."""
        # Validate file type from content-type header
        content_type = file.content_type or ""
        is_image = content_type in ALLOWED_IMAGE_TYPES
        is_doc = content_type in ALLOWED_DOC_TYPES

        if not is_image and not is_doc:
            raise HTTPException(
                status_code=400,
                detail="不支持的文件类型"
            )

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file size
        max_size = MAX_IMAGE_SIZE if is_image else MAX_FILE_SIZE
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大，最大允许 {max_size // (1024*1024)}MB"
            )

        # Validate magic bytes for images and PDFs
        if is_image or content_type == 'application/pdf':
            if not self._validate_magic_bytes(content, content_type):
                raise HTTPException(
                    status_code=400,
                    detail="文件内容与类型不匹配"
                )

        # Generate unique filename with sanitized extension
        ext = self._sanitize_extension(file.filename or "file")
        unique_name = f"{uuid.uuid4().hex}{ext}"

        # Create user directory
        user_dir = UPLOAD_DIR / str(user_id)
        user_dir.mkdir(exist_ok=True)

        file_path = user_dir / unique_name

        # Process image (compress if needed)
        if is_image:
            content = await self._process_image(content, content_type)

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        # Generate URL
        url = f"/uploads/{user_id}/{unique_name}"

        return {
            "filename": file.filename,
            "url": url,
            "file_type": content_type,
            "file_size": len(content),
            "file_path": str(file_path)
        }

    async def upload_files(self, files: List[UploadFile], user_id: int) -> List[dict]:
        """Upload multiple files."""
        results = []
        for file in files:
            result = await self.upload_file(file, user_id)
            results.append(result)
        return results

    async def _process_image(self, content: bytes, content_type: str) -> bytes:
        """Process and optionally compress image."""
        try:
            img = Image.open(io.BytesIO(content))

            # Convert RGBA to RGB for JPEG
            if img.mode == "RGBA" and content_type == "image/jpeg":
                img = img.convert("RGB")

            # Resize if too large (max 2048px on longest side)
            max_dimension = 2048
            if max(img.size) > max_dimension:
                ratio = max_dimension / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Save with compression
            output = io.BytesIO()
            format_map = {
                "image/jpeg": "JPEG",
                "image/png": "PNG",
                "image/gif": "GIF",
                "image/webp": "WEBP"
            }
            img_format = format_map.get(content_type, "JPEG")

            if img_format == "JPEG":
                img.save(output, format=img_format, quality=85, optimize=True)
            elif img_format == "PNG":
                img.save(output, format=img_format, optimize=True)
            else:
                img.save(output, format=img_format)

            return output.getvalue()
        except Exception as e:
            # Return original if processing fails
            return content

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            path = Path(file_path)
            if path.exists() and str(path).startswith(str(UPLOAD_DIR)):
                path.unlink()
                return True
            return False
        except Exception:
            return False

    def get_file_path(self, url: str) -> Optional[Path]:
        """Get file path from URL."""
        if url.startswith("/uploads/"):
            relative_path = url[9:]  # Remove "/uploads/"
            file_path = UPLOAD_DIR / relative_path
            if file_path.exists():
                return file_path
        return None


file_service = FileService()
