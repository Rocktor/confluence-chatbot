import re
import json
import os
import mimetypes
import logging
from typing import Dict, Any, List, Optional
from app.services.confluence_service import ConfluenceService
from app.services.confluence_image_service import ConfluenceImageService
from app.services.tools import (
    REVIEW_STANDARD, REVIEW_OUTPUT_FORMAT,
    EXPERIMENT_REVIEW_STANDARD, EXPERIMENT_REVIEW_OUTPUT_FORMAT,
    SLA_REVIEW_STANDARD, SLA_REVIEW_OUTPUT_FORMAT,
    MEETING_SUBMISSION_REVIEW_STANDARD, MEETING_SUBMISSION_REVIEW_OUTPUT_FORMAT
)

logger = logging.getLogger("tool_executor")


class ToolExecutor:
    """Execute AI Agent tools"""

    def __init__(self, confluence_service: Optional[ConfluenceService]):
        self.confluence = confluence_service
        # Create image download service for AI vision
        if confluence_service:
            self.image_service = ConfluenceImageService(
                base_url=confluence_service.base_url,
                auth=confluence_service.auth
            )
        else:
            self.image_service = None

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
        # Check credentials for Confluence tools (review tool can work without Confluence)
        if self.confluence is None and tool_name not in (
            "review_meeting_material", "review_experiment_retrospective", "review_sla_contract",
            "review_meeting_submission"
        ):
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
            elif tool_name == "move_confluence_page":
                return await self._move_page(arguments)
            elif tool_name == "upload_attachment_to_confluence":
                return await self._upload_attachment(arguments)
            # Table operations
            elif tool_name == "list_confluence_tables":
                return await self._list_tables(arguments)
            elif tool_name == "insert_table_column":
                return await self._insert_column(arguments)
            elif tool_name == "delete_table_column":
                return await self._delete_column(arguments)
            elif tool_name == "update_table_cell":
                return await self._update_cell(arguments)
            elif tool_name == "insert_table_row":
                return await self._insert_row(arguments)
            elif tool_name == "delete_table_row":
                return await self._delete_row(arguments)
            # Navigation tools
            elif tool_name == "list_children_pages":
                return await self._list_children(arguments)
            elif tool_name == "get_confluence_spaces":
                return await self._get_spaces(arguments)
            # Image viewing tool
            elif tool_name == "view_confluence_image":
                return await self._view_image(arguments)
            # Review tools
            elif tool_name == "review_meeting_material":
                return await self._review_meeting_material(arguments)
            elif tool_name == "review_experiment_retrospective":
                return await self._review_experiment_retrospective(arguments)
            elif tool_name == "review_sla_contract":
                return await self._review_sla_contract(arguments)
            elif tool_name == "review_meeting_submission":
                return await self._review_meeting_submission(arguments)
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
            result["image_note"] = "如需查看更多图片，可使用 view_confluence_image 工具"

        # Auto-download attachment images for AI vision (best-effort, up to 5)
        if images and self.image_service:
            try:
                downloaded = await self.image_service.download_images_batch(
                    page_id=page["id"],
                    images=images,
                    max_images=5
                )
                if downloaded:
                    result["_downloaded_images"] = [
                        {"filename": img["filename"], "data_url": img["data_url"]}
                        for img in downloaded
                    ]
                    result["_downloaded_filenames"] = [img["filename"] for img in downloaded]
                    logger.info(f"Auto-downloaded {len(downloaded)}/{len(images)} images from page {page['id']}")
            except Exception as e:
                logger.warning(f"Failed to auto-download images for AI vision: {e}")

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

    async def _move_page(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Move Confluence page to a new parent"""
        page_id = self._extract_page_id(args["page_id_or_url"])
        new_parent_id = self._extract_page_id(args["new_parent_id_or_url"])

        result = await self.confluence.move_page(page_id, new_parent_id)
        return result

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
                         "建议：1) 重新 read_confluence_page 获取最新 HTML；"
                         "2) 如果是修改表格内容，请改用 update_table_cell 工具；"
                         "3) 请勿使用 update_confluence_page 重写整个页面！"
            }

        # If new_content looks like Markdown, convert to HTML
        if new_content.strip() and not new_content.strip().startswith('<'):
            new_content = self.confluence.markdown_to_html(new_content)
        else:
            # Even for HTML content, process [image:xxx] and ![](xxx) patterns
            new_content = self.confluence._process_cell_content(new_content)

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

    # ============ Image Viewing ============

    async def _view_image(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """View a single Confluence page attachment image for AI vision"""
        page_id = args["page_id"]
        filename = args["filename"]

        if not self.image_service:
            return {"success": False, "error": "Confluence 未配置"}

        try:
            result = await self.image_service.download_attachment(page_id, filename)
        except Exception as e:
            logger.error(f"Failed to download image {filename} from page {page_id}: {e}")
            return {"success": False, "error": f"无法下载图片: {filename} ({e})"}

        if not result:
            return {"success": False, "error": f"无法下载图片: {filename}"}

        return {
            "success": True,
            "filename": filename,
            "message": f"图片 {filename} 已加载，请查看。",
            "_downloaded_images": [{"filename": filename, "data_url": result["data_url"]}]
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

    async def _update_cell(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update a specific cell in a table"""
        page_id = self._extract_page_id(args["page_id_or_url"])
        table_index = args["table_index"]
        row_index = args["row_index"]
        column_index = args["column_index"]
        content = args["content"]
        append = args.get("append", False)

        # Get current page
        page = await self.confluence.get_page(page_id)
        html_content = page.get("body", {}).get("storage", {}).get("value", "")
        current_version = page.get("version", {}).get("number", 1)

        # Update cell
        updated_html = self.confluence.update_table_cell(
            html_content, table_index, row_index, column_index, content, append
        )

        # Update page
        result = await self.confluence.update_page(page_id, page["title"], updated_html, current_version)

        return {
            "success": True,
            "page_id": result["id"],
            "title": result["title"],
            "version": result.get("version", {}).get("number"),
            "message": f"成功{'追加' if append else '更新'}表格 {table_index} 第 {row_index} 行第 {column_index} 列的内容",
            "url": f"{self.confluence.base_url}/pages/viewpage.action?pageId={result['id']}"
        }

    async def _insert_row(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new row into a table"""
        page_id = self._extract_page_id(args["page_id_or_url"])
        table_index = args["table_index"]
        row_position = args["row_position"]
        cell_values = args["cell_values"]
        is_header = args.get("is_header", False)

        # Get current page
        page = await self.confluence.get_page(page_id)
        html_content = page.get("body", {}).get("storage", {}).get("value", "")
        current_version = page.get("version", {}).get("number", 1)

        # Insert row
        updated_html = self.confluence.insert_table_row(
            html_content, table_index, row_position, cell_values, is_header
        )

        # Update page
        result = await self.confluence.update_page(page_id, page["title"], updated_html, current_version)

        return {
            "success": True,
            "page_id": result["id"],
            "title": result["title"],
            "version": result.get("version", {}).get("number"),
            "message": f"成功在表格 {table_index} 第 {row_position} 位置插入新行",
            "url": f"{self.confluence.base_url}/pages/viewpage.action?pageId={result['id']}"
        }

    async def _delete_row(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a row from a table"""
        page_id = self._extract_page_id(args["page_id_or_url"])
        table_index = args["table_index"]
        row_index = args["row_index"]

        # Get current page
        page = await self.confluence.get_page(page_id)
        html_content = page.get("body", {}).get("storage", {}).get("value", "")
        current_version = page.get("version", {}).get("number", 1)

        # Delete row
        updated_html = self.confluence.delete_table_row(html_content, table_index, row_index)

        # Update page
        result = await self.confluence.update_page(page_id, page["title"], updated_html, current_version)

        return {
            "success": True,
            "page_id": result["id"],
            "title": result["title"],
            "version": result.get("version", {}).get("number"),
            "message": f"成功删除表格 {table_index} 的第 {row_index} 行",
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

    # ============ Review Tools ============

    async def _get_review_document_content(self, args: Dict[str, Any]) -> str:
        """Extract document content for review from args (shared by all review tools)"""
        page_id_or_url = args.get("page_id_or_url")
        content = args.get("content")

        if page_id_or_url:
            if self.confluence is None:
                raise ValueError("读取 Confluence 页面需要配置凭证。请在设置中配置，或直接粘贴文档内容。")
            page_id = self._extract_page_id(page_id_or_url)
            page = await self.confluence.get_page(page_id)
            html_content = page.get("body", {}).get("storage", {}).get("value", "")
            document_content = self.confluence.html_to_markdown(html_content)
            return f"【页面标题】{page['title']}\n\n{document_content}"
        elif content:
            return content
        else:
            return "（未提供文档内容，请根据当前对话上下文中的文档内容进行审稿）"

    async def _review_meeting_material(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Review meeting material against standards"""
        try:
            document_content = await self._get_review_document_content(args)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        return {
            "success": True,
            "review_standard": REVIEW_STANDARD,
            "document_content": document_content,
            "output_format": REVIEW_OUTPUT_FORMAT,
            "instruction": "请严格按照上述审稿标准对文档进行审核，按照输出格式生成完整的审稿报告。注意：只评审材料质量，不评判业务方向。"
        }

    async def _review_experiment_retrospective(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Review experiment retrospective against standards"""
        try:
            document_content = await self._get_review_document_content(args)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        return {
            "success": True,
            "review_standard": EXPERIMENT_REVIEW_STANDARD,
            "document_content": document_content,
            "output_format": EXPERIMENT_REVIEW_OUTPUT_FORMAT,
            "instruction": "请严格按照上述运策实验复盘审稿标准对文档进行审核，按照输出格式生成完整的审稿报告。注意：只评审复盘材料质量，不评判实验本身成败。失败的实验如果复盘写得好，同样可以高分通过。"
        }

    async def _review_sla_contract(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Review SLA contract against standards"""
        try:
            document_content = await self._get_review_document_content(args)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        return {
            "success": True,
            "review_standard": SLA_REVIEW_STANDARD,
            "document_content": document_content,
            "output_format": SLA_REVIEW_OUTPUT_FORMAT,
            "instruction": "请严格按照上述SLA合同审稿标准对合同进行审核，按照输出格式生成完整的审稿报告。请先判断合同类型（人力买断/增量价值分成/计件/里程碑），再进行对应的专项检查。"
        }

    async def _review_meeting_submission(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Review meeting submission material against standards"""
        try:
            document_content = await self._get_review_document_content(args)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        return {
            "success": True,
            "review_standard": MEETING_SUBMISSION_REVIEW_STANDARD,
            "document_content": document_content,
            "output_format": MEETING_SUBMISSION_REVIEW_OUTPUT_FORMAT,
            "instruction": "请严格按照 Gate+Score 审核规范逐项检查文档，按照输出格式生成完整的10分制审核报告。审核流程：1）先完成底线层4项检查（三层结构、复盘三要素、计划格式、指标口径），任一不过即判定不通过；2）底线层全部通过后进入上限层4项评级；3）结合CEO判定模式（19条驳回触发器+12条通过信号）进行风险预判；4）给出三态结论（通过/条件通过/不通过）+ 质量等级 + 评分明细 + 具体修改建议。"
        }
