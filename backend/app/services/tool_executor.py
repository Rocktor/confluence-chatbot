import re
import json
import os
import mimetypes
import logging
from typing import Dict, Any, List, Optional
from app.services.confluence_service import ConfluenceService
from app.services.confluence_image_service import ConfluenceImageService

logger = logging.getLogger("tool_executor")


class ToolExecutor:
    """Execute AI Agent tools"""

    def __init__(self, confluence_service: Optional[ConfluenceService]):
        self.confluence = confluence_service
        # Initialize image service if confluence service is available
        self.image_service = None
        if confluence_service:
            self.image_service = ConfluenceImageService(
                base_url=confluence_service.base_url,
                auth=confluence_service.auth
            )

    def _extract_page_id(self, page_id_or_url: str) -> str:
        """Extract page ID from URL or return as-is"""
        if 'pageId=' in page_id_or_url:
            match = re.search(r'pageId=(\d+)', page_id_or_url)
            if match:
                return match.group(1)
        return page_id_or_url

    def _extract_images(self, html_content: str, page_id: str) -> List[Dict[str, str]]:
        """Extract images from Confluence HTML content"""
        images = []
        seen_filenames = set()

        # Pattern 1: <ri:attachment ri:filename="xxx"/>
        attachment_pattern = r'<ri:attachment[^>]*ri:filename="([^"]+)"'
        for match in re.finditer(attachment_pattern, html_content):
            filename = match.group(1)
            if filename not in seen_filenames:
                seen_filenames.add(filename)
                images.append({
                    "filename": filename,
                    "type": "attachment"
                })

        # Pattern 2: ri:filename="xxx" (attribute in different order)
        filename_pattern = r'ri:filename="([^"]+)"'
        for match in re.finditer(filename_pattern, html_content):
            filename = match.group(1)
            if filename not in seen_filenames and self._is_image_file(filename):
                seen_filenames.add(filename)
                images.append({
                    "filename": filename,
                    "type": "attachment"
                })

        # Pattern 3: <ri:url ri:value="xxx"/>
        url_pattern = r'<ri:url[^>]*ri:value="([^"]+)"'
        for match in re.finditer(url_pattern, html_content):
            url = match.group(1)
            if url not in seen_filenames:
                seen_filenames.add(url)
                if not url.startswith(('http://', 'https://')):
                    images.append({
                        "filename": url,
                        "type": "attachment"
                    })
                elif self._is_image_url(url):
                    images.append({
                        "filename": url,
                        "type": "external"
                    })

        # Pattern 4: <ac:image> tags with embedded content
        ac_image_pattern = r'<ac:image[^>]*>.*?</ac:image>'
        for match in re.finditer(ac_image_pattern, html_content, re.DOTALL):
            image_tag = match.group(0)
            # Extract filename from within the ac:image tag
            inner_filename = re.search(r'ri:filename="([^"]+)"', image_tag)
            if inner_filename:
                filename = inner_filename.group(1)
                if filename not in seen_filenames:
                    seen_filenames.add(filename)
                    images.append({
                        "filename": filename,
                        "type": "attachment"
                    })

        logger.info(f"Extracted {len(images)} images from page {page_id}: {[img['filename'] for img in images]}")
        return images

    def _is_image_file(self, filename: str) -> bool:
        """Check if filename looks like an image"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return ext in ('png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp')

    def _is_image_url(self, url: str) -> bool:
        """Check if URL points to an image"""
        return self._is_image_file(url.split('?')[0])

    def _fix_image_references(self, html_content: str, attachment_filenames: List[str]) -> str:
        """Convert ri:url to ri:attachment for known attachments"""
        for filename in attachment_filenames:
            # Replace <ri:url ri:value="filename"/> with <ri:attachment ri:filename="filename"/>
            html_content = re.sub(
                rf'<ri:url\s+ri:value="{re.escape(filename)}"[^/]*/?>',
                f'<ri:attachment ri:filename="{filename}"/>',
                html_content
            )
        return html_content

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return result"""
        # Check credentials for Confluence tools
        if self.confluence is None:
            return {
                "success": False,
                "error": "您尚未配置 Confluence 凭证。请在设置中配置您的 Confluence 账号信息后再试。"
            }

        try:
            if tool_name == "read_confluence_page":
                return await self._read_page(arguments)
            elif tool_name == "insert_content_to_confluence_page":
                return await self._insert_content(arguments)
            elif tool_name == "update_confluence_page":
                return await self._update_page(arguments)
            elif tool_name == "edit_confluence_page":
                return await self._edit_page(arguments)
            elif tool_name == "create_confluence_page":
                return await self._create_page(arguments)
            elif tool_name == "search_confluence":
                return await self._search(arguments)
            elif tool_name == "upload_attachment_to_confluence":
                return await self._upload_attachment(arguments)
            # Table operations
            elif tool_name == "list_confluence_tables":
                return await self._list_tables(arguments)
            elif tool_name == "insert_table_column":
                return await self._insert_column(arguments)
            elif tool_name == "delete_table_column":
                return await self._delete_column(arguments)
            # Navigation tools
            elif tool_name == "list_children_pages":
                return await self._list_children(arguments)
            elif tool_name == "get_confluence_spaces":
                return await self._get_spaces(arguments)
            # Image analysis
            elif tool_name == "analyze_confluence_images":
                return await self._analyze_images(arguments)
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _read_page(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read Confluence page"""
        page_id = self._extract_page_id(args["page_id_or_url"])
        page = await self.confluence.get_page(page_id)

        html_content = page.get("body", {}).get("storage", {}).get("value", "")
        markdown_content = self.confluence.html_to_markdown(html_content)

        # Extract images from HTML
        images = self._extract_images(html_content, page_id)

        # Limit content length to avoid context overflow (~8000 chars ≈ 2000 tokens)
        MAX_CONTENT_LENGTH = 8000
        truncated = False
        if len(markdown_content) > MAX_CONTENT_LENGTH:
            markdown_content = markdown_content[:MAX_CONTENT_LENGTH] + "\n\n...(内容已截断，原文过长)"
            truncated = True

        # Truncate HTML for context (keep structure markers)
        MAX_HTML_LENGTH = 12000
        html_truncated = html_content
        if len(html_content) > MAX_HTML_LENGTH:
            html_truncated = html_content[:MAX_HTML_LENGTH] + "\n<!-- ... HTML 已截断 -->"

        result = {
            "success": True,
            "page_id": page["id"],
            "title": page["title"],
            "space_key": page.get("space", {}).get("key", ""),
            "version": page.get("version", {}).get("number", 1),
            "content": markdown_content,
            "html": html_truncated,  # 原始 HTML（用于精确编辑）
            "truncated": truncated,
            "url": f"{self.confluence.base_url}/pages/viewpage.action?pageId={page['id']}"
        }

        # Add images info if present
        if images:
            result["images"] = images
            result["image_note"] = "精确编辑时使用 edit_confluence_page，从 html 字段中找到要修改的部分"

        return result

    async def _insert_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Insert content at the beginning or end of a Confluence page, preserving original content"""
        page_id = self._extract_page_id(args["page_id_or_url"])
        position = args.get("position", "prepend")

        # Get current page
        current_page = await self.confluence.get_page(page_id)
        current_version = current_page.get("version", {}).get("number", 1)
        title = current_page["title"]
        current_html = current_page.get("body", {}).get("storage", {}).get("value", "")

        # Convert new content to HTML
        new_html = self.confluence.markdown_to_html(args["content"])

        # Insert at the specified position
        if position == "prepend":
            combined_html = new_html + current_html
        else:  # append
            combined_html = current_html + new_html

        # Update page
        result = await self.confluence.update_page(page_id, title, combined_html, current_version)

        return {
            "success": True,
            "page_id": result["id"],
            "title": result["title"],
            "version": result.get("version", {}).get("number"),
            "url": f"{self.confluence.base_url}/pages/viewpage.action?pageId={result['id']}",
            "position": position
        }

    async def _update_page(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update Confluence page"""
        page_id = self._extract_page_id(args["page_id_or_url"])

        # Get current page for version, title, and existing attachments
        current_page = await self.confluence.get_page(page_id)
        current_version = current_page.get("version", {}).get("number", 1)
        title = args.get("title") or current_page["title"]

        # Extract existing attachment filenames from current page
        current_html = current_page.get("body", {}).get("storage", {}).get("value", "")
        existing_images = self._extract_images(current_html, page_id)
        attachment_filenames = [img["filename"] for img in existing_images if img["type"] == "attachment"]
        logger.info(f"Existing attachments: {attachment_filenames}")

        # Convert markdown to HTML
        html_content = self.confluence.markdown_to_html(args["content"])
        logger.info(f"HTML after markdown_to_html (first 500): {html_content[:500]}")

        # Fix image references: convert ri:url to ri:attachment for known attachments
        if attachment_filenames:
            html_content = self._fix_image_references(html_content, attachment_filenames)
            logger.info(f"HTML after fix_image_references (first 500): {html_content[:500]}")

        # Update page
        result = await self.confluence.update_page(page_id, title, html_content, current_version)

        return {
            "success": True,
            "page_id": result["id"],
            "title": result["title"],
            "version": result.get("version", {}).get("number"),
            "url": f"{self.confluence.base_url}/pages/viewpage.action?pageId={result['id']}"
        }

    async def _create_page(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create new Confluence page"""
        html_content = self.confluence.markdown_to_html(args["content"])

        result = await self.confluence.create_page(
            space_key=args["space_key"],
            title=args["title"],
            content=html_content,
            parent_id=args.get("parent_id")
        )

        return {
            "success": True,
            "page_id": result["id"],
            "title": result["title"],
            "url": f"{self.confluence.base_url}/pages/viewpage.action?pageId={result['id']}"
        }

    async def _search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search Confluence pages"""
        results = await self.confluence.search_pages(
            query=args["keyword"],
            space_key=args.get("space_key")
        )

        return {
            "success": True,
            "count": len(results),
            "results": results
        }

    async def _upload_attachment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Upload attachment to Confluence page"""
        page_id = args["page_id"]
        file_url = args["file_url"]

        # Convert URL to file path (e.g., /uploads/1/file.jpg -> /app/uploads/1/file.jpg)
        if file_url.startswith('/uploads/'):
            file_path = f"/app{file_url}"
        elif file_url.startswith('uploads/'):
            file_path = f"/app/{file_url}"
        else:
            file_path = file_url

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        filename = os.path.basename(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or "application/octet-stream"

        result = await self.confluence.upload_attachment(page_id, file_path, filename, content_type)
        return result

    async def _edit_page(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Precise edit: find and replace in original HTML"""
        page_id = self._extract_page_id(args["page_id_or_url"])
        old_content = args["old_content"]
        new_content = args["new_content"]

        # Get current page
        current_page = await self.confluence.get_page(page_id)
        current_html = current_page.get("body", {}).get("storage", {}).get("value", "")
        current_version = current_page.get("version", {}).get("number", 1)

        # Check if old_content exists
        if old_content not in current_html:
            return {
                "success": False,
                "error": "未找到要替换的内容。请确保 old_content 与页面中的 HTML 完全匹配。"
            }

        # If new_content looks like Markdown, convert to HTML
        if new_content.strip() and not new_content.strip().startswith('<'):
            new_content = self.confluence.markdown_to_html(new_content)

        # Precise replacement (only first occurrence)
        updated_html = current_html.replace(old_content, new_content, 1)

        # Update page
        result = await self.confluence.update_page(
            page_id,
            current_page["title"],
            updated_html,
            current_version
        )

        return {
            "success": True,
            "page_id": result["id"],
            "title": result["title"],
            "version": result.get("version", {}).get("number"),
            "message": "内容已精确替换",
            "url": f"{self.confluence.base_url}/pages/viewpage.action?pageId={result['id']}"
        }

    # ============ Table Operations ============

    async def _list_tables(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all tables in a Confluence page"""
        page_id = self._extract_page_id(args["page_id_or_url"])

        # Get page HTML
        page = await self.confluence.get_page(page_id)
        html_content = page.get("body", {}).get("storage", {}).get("value", "")

        # Parse tables
        tables = self.confluence.list_tables(html_content)

        return {
            "success": True,
            "page_id": page_id,
            "title": page["title"],
            "table_count": len(tables),
            "tables": tables
        }

    async def _insert_column(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a column into a table"""
        page_id = self._extract_page_id(args["page_id_or_url"])
        table_index = args["table_index"]
        column_position = args["column_position"]
        column_name = args["column_name"]
        default_value = args.get("default_value", "")

        # Get current page
        page = await self.confluence.get_page(page_id)
        html_content = page.get("body", {}).get("storage", {}).get("value", "")
        current_version = page.get("version", {}).get("number", 1)

        # Insert column
        updated_html = self.confluence.insert_table_column(
            html_content, table_index, column_position, column_name, default_value
        )

        # Update page
        result = await self.confluence.update_page(page_id, page["title"], updated_html, current_version)

        return {
            "success": True,
            "page_id": result["id"],
            "title": result["title"],
            "version": result.get("version", {}).get("number"),
            "message": f"成功在表格 {table_index} 的第 {column_position} 列位置插入列 '{column_name}'",
            "url": f"{self.confluence.base_url}/pages/viewpage.action?pageId={result['id']}"
        }

    async def _delete_column(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a column from a table"""
        page_id = self._extract_page_id(args["page_id_or_url"])
        table_index = args["table_index"]
        column_position = args["column_position"]

        # Get current page
        page = await self.confluence.get_page(page_id)
        html_content = page.get("body", {}).get("storage", {}).get("value", "")
        current_version = page.get("version", {}).get("number", 1)

        # Delete column
        updated_html = self.confluence.delete_table_column(html_content, table_index, column_position)

        # Update page
        result = await self.confluence.update_page(page_id, page["title"], updated_html, current_version)

        return {
            "success": True,
            "page_id": result["id"],
            "title": result["title"],
            "version": result.get("version", {}).get("number"),
            "message": f"成功删除表格 {table_index} 的第 {column_position} 列",
            "url": f"{self.confluence.base_url}/pages/viewpage.action?pageId={result['id']}"
        }

    # ============ Navigation Tools ============

    async def _list_children(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List child pages"""
        page_id = self._extract_page_id(args["page_id_or_url"])

        children = await self.confluence.list_children(page_id)

        return {
            "success": True,
            "parent_page_id": page_id,
            "count": len(children),
            "children": children
        }

    async def _get_spaces(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get Confluence spaces"""
        spaces = await self.confluence.get_spaces()

        return {
            "success": True,
            "count": len(spaces),
            "spaces": spaces
        }

    # ============ Image Analysis ============

    async def _analyze_images(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze images from a Confluence page"""
        page_id = args["page_id"]
        requested_filenames = args.get("image_filenames", [])

        if not self.image_service:
            return {
                "success": False,
                "error": "图片服务未初始化，请先配置 Confluence 凭证"
            }

        # Get page to retrieve image list
        page = await self.confluence.get_page(page_id)
        html_content = page.get("body", {}).get("storage", {}).get("value", "")

        # Extract images from HTML
        images = self._extract_images(html_content, page_id)

        if not images:
            return {
                "success": False,
                "error": "页面中没有找到图片"
            }

        # Filter by requested filenames if specified
        if requested_filenames:
            images = [img for img in images if img["filename"] in requested_filenames]
            if not images:
                return {
                    "success": False,
                    "error": f"未找到指定的图片: {requested_filenames}"
                }

        # Download and process images
        downloaded_images = await self.image_service.download_images_batch(page_id, images, max_images=5)

        if not downloaded_images:
            return {
                "success": False,
                "error": "无法下载任何图片，请检查图片是否存在或权限是否正确"
            }

        # Return with multimodal flag for chat_service to handle
        return {
            "success": True,
            "_multimodal": True,
            "page_id": page_id,
            "title": page.get("title", ""),
            "image_count": len(downloaded_images),
            "images": downloaded_images,
            "message": f"已加载 {len(downloaded_images)} 张图片，正在解读..."
        }
