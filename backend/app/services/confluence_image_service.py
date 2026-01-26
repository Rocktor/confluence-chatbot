"""
Confluence Image Service - Download and process images from Confluence pages
"""

import base64
import hashlib
import httpx
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote
from PIL import Image
from io import BytesIO
from app.utils.logger import setup_logger

logger = setup_logger("confluence_image_service")

# Supported image formats
SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_DIMENSION = 1024  # Max width/height for compression
JPEG_QUALITY = 85


class ConfluenceImageService:
    """Download and process images from Confluence attachments"""

    def __init__(self, base_url: str, auth: Tuple[str, str], cache_dir: str = "/app/cache/confluence_images"):
        """
        Initialize the image service

        Args:
            base_url: Confluence base URL (e.g., https://docs.example.com)
            auth: Tuple of (username, api_token) for authentication
            cache_dir: Directory to cache downloaded images
        """
        self.base_url = base_url.rstrip('/')
        self.auth = auth  # Keep as tuple for httpx
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, page_id: str, filename: str) -> Path:
        """Generate a unique cache path for an image"""
        # Create a hash to avoid filename collisions
        hash_input = f"{page_id}_{filename}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            ext = '.jpg'
        return self.cache_dir / f"{page_id}_{file_hash}{ext}"

    def _is_supported_format(self, filename: str) -> bool:
        """Check if the file format is supported"""
        ext = Path(filename).suffix.lower()
        return ext in SUPPORTED_FORMATS

    async def download_attachment(self, page_id: str, filename: str) -> Optional[Dict]:
        """
        Download an attachment image from Confluence

        Args:
            page_id: The Confluence page ID
            filename: The attachment filename

        Returns:
            Dict with image info: {filename, local_path, base64, data_url, width, height}
            or None if download failed
        """
        if not self._is_supported_format(filename):
            logger.warning(f"Unsupported image format: {filename}")
            return None

        cache_path = self._get_cache_path(page_id, filename)

        # Check cache first
        if cache_path.exists():
            logger.info(f"Cache hit: {filename}")
            return await self._process_cached_image(cache_path, filename)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Get attachment info via REST API
                api_url = f"{self.base_url}/rest/api/content/{page_id}/child/attachment"
                logger.info(f"Fetching attachments list from: {api_url}")

                response = await client.get(
                    api_url,
                    auth=self.auth,
                    params={"os_authType": "basic", "filename": filename, "expand": "version,container"}
                )

                if response.status_code != 200:
                    logger.error(f"Failed to get attachment info: {response.status_code}")
                    return None

                attachments = response.json().get('results', [])
                if not attachments:
                    logger.error(f"Attachment not found: {filename}")
                    return None

                # Find the matching attachment
                attachment = None
                for att in attachments:
                    if att.get('title') == filename:
                        attachment = att
                        break

                if not attachment:
                    logger.error(f"Attachment not found in results: {filename}")
                    return None

                # Step 2: Download using the attachment's download link
                download_link = attachment.get('_links', {}).get('download', '')
                if not download_link:
                    logger.error(f"No download link for: {filename}")
                    return None

                # Build full download URL
                download_url = f"{self.base_url}{download_link}"
                logger.info(f"Downloading attachment: {download_url}")

                download_response = await client.get(
                    download_url,
                    auth=self.auth,
                    params={"os_authType": "basic"},
                    follow_redirects=True
                )

                if download_response.status_code != 200:
                    logger.error(f"Download failed: {download_response.status_code} for {filename}")
                    return None

                content_length = len(download_response.content)
                if content_length > MAX_IMAGE_SIZE:
                    logger.warning(f"Image too large ({content_length} bytes): {filename}")
                    return None

                image_data = download_response.content
                logger.info(f"Downloaded {filename}: {content_length} bytes")

            # Process and save image
            return await self._process_and_save_image(image_data, cache_path, filename)

        except httpx.TimeoutException:
            logger.error(f"Download timeout: {filename}")
            return None
        except Exception as e:
            logger.error(f"Download error for {filename}: {e}")
            return None

    async def _process_and_save_image(self, image_data: bytes, cache_path: Path, filename: str) -> Optional[Dict]:
        """Process image: compress if needed and save to cache"""
        try:
            # Open image with PIL
            img = Image.open(BytesIO(image_data))
            original_format = img.format
            width, height = img.size

            # Resize if too large
            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                ratio = min(MAX_DIMENSION / width, MAX_DIMENSION / height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                width, height = new_size
                logger.info(f"Resized {filename} to {width}x{height}")

            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'P') and cache_path.suffix.lower() in ('.jpg', '.jpeg'):
                img = img.convert('RGB')

            # Save compressed image
            output = BytesIO()
            if cache_path.suffix.lower() in ('.jpg', '.jpeg'):
                img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
            elif cache_path.suffix.lower() == '.png':
                img.save(output, format='PNG', optimize=True)
            elif cache_path.suffix.lower() == '.webp':
                img.save(output, format='WEBP', quality=JPEG_QUALITY)
            else:
                img.save(output, format=original_format or 'JPEG')

            compressed_data = output.getvalue()

            # Save to cache
            cache_path.write_bytes(compressed_data)
            logger.info(f"Cached: {filename} ({len(compressed_data)} bytes)")

            # Generate base64
            b64_data = base64.b64encode(compressed_data).decode('utf-8')
            mime_type = self._get_mime_type(cache_path.suffix)

            return {
                "filename": filename,
                "local_path": str(cache_path),
                "base64": b64_data,
                "data_url": f"data:{mime_type};base64,{b64_data}",
                "width": width,
                "height": height
            }

        except Exception as e:
            logger.error(f"Image processing error for {filename}: {e}")
            return None

    async def _process_cached_image(self, cache_path: Path, filename: str) -> Optional[Dict]:
        """Process a cached image file"""
        try:
            image_data = cache_path.read_bytes()
            img = Image.open(BytesIO(image_data))
            width, height = img.size

            b64_data = base64.b64encode(image_data).decode('utf-8')
            mime_type = self._get_mime_type(cache_path.suffix)

            return {
                "filename": filename,
                "local_path": str(cache_path),
                "base64": b64_data,
                "data_url": f"data:{mime_type};base64,{b64_data}",
                "width": width,
                "height": height
            }
        except Exception as e:
            logger.error(f"Cache read error for {filename}: {e}")
            # Remove corrupted cache file
            cache_path.unlink(missing_ok=True)
            return None

    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type from file extension"""
        mime_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_map.get(extension.lower(), 'image/jpeg')

    async def download_images_batch(
        self,
        page_id: str,
        images: List[Dict],
        max_images: int = 5
    ) -> List[Dict]:
        """
        Download multiple images in batch

        Args:
            page_id: The Confluence page ID
            images: List of image info dicts with 'filename' and 'type'
            max_images: Maximum number of images to download

        Returns:
            List of successfully downloaded image info dicts
        """
        results = []

        # Filter to attachment images only and limit count
        attachment_images = [
            img for img in images
            if img.get('type') == 'attachment' and self._is_supported_format(img.get('filename', ''))
        ][:max_images]

        for img in attachment_images:
            result = await self.download_attachment(page_id, img['filename'])
            if result:
                results.append(result)

        logger.info(f"Downloaded {len(results)}/{len(attachment_images)} images for page {page_id}")
        return results

    async def download_external_image(self, url: str) -> Optional[Dict]:
        """
        Download an external image by URL

        Args:
            url: The image URL

        Returns:
            Dict with image info or None if failed
        """
        try:
            # Generate cache path from URL
            url_hash = hashlib.md5(url.encode()).hexdigest()
            ext = Path(url).suffix.lower()
            if ext not in SUPPORTED_FORMATS:
                ext = '.jpg'
            cache_path = self.cache_dir / f"external_{url_hash}{ext}"

            # Check cache
            if cache_path.exists():
                logger.info(f"Cache hit for external: {url}")
                return await self._process_cached_image(cache_path, Path(url).name)

            # Download using httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                if response.status_code != 200:
                    logger.error(f"External download failed: {response.status_code}")
                    return None

                image_data = response.content

            return await self._process_and_save_image(image_data, cache_path, Path(url).name)

        except Exception as e:
            logger.error(f"External image download error: {e}")
            return None
