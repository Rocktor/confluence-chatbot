import httpx
import re
import html
from html import unescape
from typing import Dict, Optional
from cryptography.fernet import Fernet
import base64
import hashlib
from app.config import settings


class ConfluenceService:
    def __init__(self, base_url: str, username: str, api_key: str = None, password: str = None):
        # All parameters are required (no fallback to global config)
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_key = api_key
        self.password = password

        # Use API key if available, otherwise password
        auth_credential = self.api_key if self.api_key else self.password
        if not auth_credential:
            raise ValueError("Either api_key or password must be provided")
        self.auth = (self.username, auth_credential)

    @staticmethod
    def encrypt_token(token: str) -> str:
        """Encrypt API token"""
        key = hashlib.sha256(settings.JWT_SECRET.encode()).digest()
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.encrypt(token.encode()).decode()

    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """Decrypt API token"""
        key = hashlib.sha256(settings.JWT_SECRET.encode()).digest()
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.decrypt(encrypted_token.encode()).decode()

    async def get_page(self, page_id: str) -> Dict:
        """Get Confluence page"""
        url = f"{self.base_url}/rest/api/content/{page_id}"
        params = {"expand": "body.storage,version,space", "os_authType": "basic"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            return response.json()

    async def create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> Dict:
        """Create Confluence page"""
        url = f"{self.base_url}/rest/api/content"
        params = {"os_authType": "basic"}

        data = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }

        if parent_id:
            data["ancestors"] = [{"id": parent_id}]

        async with httpx.AsyncClient() as client:
            response = await client.post(url, auth=self.auth, json=data, params=params)
            response.raise_for_status()
            return response.json()

    async def update_page(
        self,
        page_id: str,
        title: str,
        content: str,
        version: int
    ) -> Dict:
        """Update Confluence page"""
        url = f"{self.base_url}/rest/api/content/{page_id}"
        params = {"os_authType": "basic"}

        data = {
            "version": {"number": version + 1},
            "title": title,
            "type": "page",
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.put(url, auth=self.auth, json=data, params=params)
            response.raise_for_status()
            return response.json()

    async def delete_page(self, page_id: str) -> bool:
        """Delete Confluence page"""
        url = f"{self.base_url}/rest/api/content/{page_id}"
        params = {"os_authType": "basic"}

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, auth=self.auth, params=params)
            response.raise_for_status()
            return True

    async def search_pages(self, query: str, space_key: Optional[str] = None, limit: int = 25) -> list:
        """Search Confluence pages by text query"""
        # Build CQL query
        cql_parts = [f'text ~ "{query}"']
        if space_key:
            cql_parts.append(f'space = "{space_key}"')
        cql_parts.append('type = page')

        cql = ' AND '.join(cql_parts)
        url = f"{self.base_url}/rest/api/content/search"
        params = {"cql": cql, "limit": limit, "expand": "space", "os_authType": "basic"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append({
                    "id": item["id"],
                    "title": item["title"],
                    "spaceKey": item.get("space", {}).get("key", ""),
                    "url": f"{self.base_url}/pages/viewpage.action?pageId={item['id']}"
                })
            return results

    async def upload_attachment(self, page_id: str, file_path: str, filename: str, content_type: str = "application/octet-stream") -> Dict:
        """Upload attachment to Confluence page"""
        url = f"{self.base_url}/rest/api/content/{page_id}/child/attachment"
        params = {"os_authType": "basic"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Check existing attachments
            response = await client.get(url, auth=self.auth, params=params)
            existing = {}
            if response.status_code == 200:
                existing = {a['title']: a['id'] for a in response.json().get('results', [])}

            with open(file_path, 'rb') as f:
                file_content = f.read()

            files = {'file': (filename, file_content, content_type)}
            headers = {"X-Atlassian-Token": "nocheck"}

            if filename in existing:
                # Update existing attachment
                att_id = existing[filename]
                update_url = f"{self.base_url}/rest/api/content/{page_id}/child/attachment/{att_id}/data"
                response = await client.post(update_url, files=files, params=params, auth=self.auth, headers=headers)
            else:
                # Create new attachment
                response = await client.post(url, files=files, params=params, auth=self.auth, headers=headers)

            if response.status_code in [200, 201]:
                result = response.json()
                if 'results' in result and len(result['results']) > 0:
                    att = result['results'][0]
                    return {
                        "success": True,
                        "id": att.get('id'),
                        "filename": filename,
                        "url": f"{self.base_url}/download/attachments/{page_id}/{filename}"
                    }
                return {"success": True, "filename": filename}
            else:
                return {"success": False, "error": f"Upload failed: {response.status_code}"}

    async def fix_image_references(self, page_id: str, filenames: list) -> Dict:
        """Fix image references in page to use attachment format"""
        page = await self.get_page(page_id)
        html_content = page['body']['storage']['value']
        version = page['version']['number']
        title = page['title']

        # Replace ri:url with ri:attachment for uploaded files
        for filename in filenames:
            # Pattern: <ac:image><ri:url ri:value="filename"/></ac:image>
            html_content = re.sub(
                rf'<ac:image><ri:url ri:value="{re.escape(filename)}"[^/]*/></ac:image>',
                f'<ac:image><ri:attachment ri:filename="{filename}"/></ac:image>',
                html_content
            )

        # Update page
        return await self.update_page(page_id, title, html_content, version)

    async def get_current_user(self) -> Dict:
        """Get current authenticated user info"""
        url = f"{self.base_url}/rest/api/user/current"
        params = {"os_authType": "basic"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            return response.json()

    def html_to_markdown(self, html_content: str) -> str:
        """Convert Confluence HTML to Markdown"""
        content = html_content

        # Headers
        for i in range(6, 0, -1):
            content = re.sub(rf'<h{i}[^>]*>(.*?)</h{i}>', rf'{"#" * i} \1\n', content, flags=re.DOTALL)

        # Bold and italic
        content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL)
        content = re.sub(r'<b>(.*?)</b>', r'**\1**', content, flags=re.DOTALL)
        content = re.sub(r'<em>(.*?)</em>', r'*\1*', content, flags=re.DOTALL)
        content = re.sub(r'<i>(.*?)</i>', r'*\1*', content, flags=re.DOTALL)

        # Inline code
        content = re.sub(r'<code>(.*?)</code>', r'`\1`', content, flags=re.DOTALL)

        # Links
        content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', content, flags=re.DOTALL)

        # Images
        content = re.sub(
            r'<ac:image[^>]*>.*?<ri:url ri:value="([^"]+)"[^>]*/?>.*?</ac:image>',
            r'![](\1)',
            content, flags=re.DOTALL
        )

        # Lists
        content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', content, flags=re.DOTALL)
        content = re.sub(r'</?[uo]l[^>]*>', '', content)

        # Blockquotes
        content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1\n', content, flags=re.DOTALL)

        # Tables
        def convert_table(match):
            table_html = match.group(0)
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, flags=re.DOTALL)
            md_rows = []
            for i, row in enumerate(rows):
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, flags=re.DOTALL)
                cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                md_rows.append('| ' + ' | '.join(cells) + ' |')
                if i == 0:
                    md_rows.append('|' + '|'.join(['---'] * len(cells)) + '|')
            return '\n'.join(md_rows) + '\n'

        content = re.sub(r'<table[^>]*>.*?</table>', convert_table, content, flags=re.DOTALL)

        # Code blocks
        def convert_code(match):
            lang = ''
            lang_match = re.search(r'ac:parameter[^>]*ac:name="language"[^>]*>([^<]+)<', match.group(0))
            if lang_match:
                lang = lang_match.group(1)
            code = match.group(1)
            return f'```{lang}\n{code}\n```\n'
        content = re.sub(
            r'<ac:structured-macro[^>]*ac:name="code"[^>]*>.*?<ac:plain-text-body><!\[CDATA\[(.*?)\]\]></ac:plain-text-body></ac:structured-macro>',
            convert_code, content, flags=re.DOTALL
        )

        # Paragraphs
        content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n', content, flags=re.DOTALL)

        # Clean remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)

        # HTML entities
        content = unescape(content)

        # Multiple blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content.strip()

    def markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown to Confluence HTML"""
        # Remove consecutive empty lines, keep at most one
        import re as regex
        markdown_content = regex.sub(r'\n{3,}', '\n\n', markdown_content.strip())

        lines = markdown_content.split('\n')
        html_lines = []
        in_code_block = False
        in_table = False
        in_list = False
        list_type = None
        code_lang = ''
        code_content = []
        prev_was_block = False  # Track if previous line was a block element (heading, list, etc.)

        for line in lines:
            # Code block handling
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_lang = line.strip()[3:].lower()
                    code_content = []
                else:
                    in_code_block = False
                    content = '\n'.join(code_content)
                    lang_param = f'<ac:parameter ac:name="language">{code_lang}</ac:parameter>' if code_lang else ''
                    html_lines.append(f'<ac:structured-macro ac:name="code">{lang_param}<ac:plain-text-body><![CDATA[{content}]]></ac:plain-text-body></ac:structured-macro>')
                    code_lang = ''
                continue

            if in_code_block:
                code_content.append(line)
                continue

            # Close list if current line is not a list item
            stripped = line.strip()
            is_ul_item = stripped.startswith('- ') or stripped.startswith('* ')
            is_ol_item = re.match(r'^\d+\.\s', stripped)

            if in_list and not is_ul_item and not is_ol_item:
                html_lines.append(f'</{list_type}>')
                in_list = False
                list_type = None

            # Table handling
            if stripped.startswith('|') and stripped.endswith('|'):
                cells = [c.strip() for c in stripped[1:-1].split('|')]
                if all(set(c) <= set('-: ') for c in cells):
                    continue

                if not in_table:
                    in_table = True
                    html_lines.append('<table><tbody>')
                    # Process cell content for images and Markdown
                    row = '<tr>' + ''.join(f'<th>{self._process_cell_content(c)}</th>' for c in cells) + '</tr>'
                else:
                    row = '<tr>' + ''.join(f'<td>{self._process_cell_content(c)}</td>' for c in cells) + '</tr>'
                html_lines.append(row)
                continue
            elif in_table:
                in_table = False
                html_lines.append('</tbody></table>')

            # Escape and process inline formats
            escaped_line = html.escape(line)
            escaped_line = self._process_inline_formats(escaped_line)

            # Block elements
            if not escaped_line.strip():
                # Skip empty lines after block elements (headings, lists, tables)
                # Only add paragraph break between text paragraphs
                if not prev_was_block and html_lines and not html_lines[-1].startswith('<p></p>'):
                    html_lines.append('<p></p>')
                prev_was_block = False
            elif escaped_line.startswith('# '):
                html_lines.append(f'<h1>{escaped_line[2:]}</h1>')
                prev_was_block = True
            elif escaped_line.startswith('## '):
                html_lines.append(f'<h2>{escaped_line[3:]}</h2>')
                prev_was_block = True
            elif escaped_line.startswith('### '):
                html_lines.append(f'<h3>{escaped_line[4:]}</h3>')
                prev_was_block = True
            elif escaped_line.startswith('#### '):
                html_lines.append(f'<h4>{escaped_line[5:]}</h4>')
                prev_was_block = True
            elif escaped_line.startswith('##### '):
                html_lines.append(f'<h5>{escaped_line[6:]}</h5>')
                prev_was_block = True
            elif escaped_line.startswith('###### '):
                html_lines.append(f'<h6>{escaped_line[7:]}</h6>')
                prev_was_block = True
            elif escaped_line.startswith('&gt; '):
                html_lines.append(f'<blockquote><p>{escaped_line[5:]}</p></blockquote>')
                prev_was_block = True
            elif is_ul_item:
                if not in_list or list_type != 'ul':
                    if in_list:
                        html_lines.append(f'</{list_type}>')
                    html_lines.append('<ul>')
                    in_list = True
                    list_type = 'ul'
                content = escaped_line[2:] if escaped_line.startswith('- ') else escaped_line[2:]
                html_lines.append(f'<li>{content}</li>')
                prev_was_block = True
            elif is_ol_item:
                if not in_list or list_type != 'ol':
                    if in_list:
                        html_lines.append(f'</{list_type}>')
                    html_lines.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                content = re.sub(r'^\d+\.\s', '', escaped_line)
                html_lines.append(f'<li>{content}</li>')
                prev_was_block = True
            else:
                html_lines.append(f'<p>{escaped_line}</p>')
                prev_was_block = False

        # Close unclosed tags
        if in_table:
            html_lines.append('</tbody></table>')
        if in_list:
            html_lines.append(f'</{list_type}>')

        return '\n'.join(html_lines)

    def _process_inline_formats(self, line: str) -> str:
        """Process inline formats (bold, italic, code, links, images)"""
        # Images ![alt](url)
        line = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            r'<ac:image><ri:url ri:value="\2"/></ac:image>',
            line
        )
        # Links [text](url)
        line = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            r'<a href="\2">\1</a>',
            line
        )
        # Bold **text**
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        # Italic *text*
        line = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', line)
        # Inline code `code`
        line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)

        return line

    # ============ Navigation Methods ============

    async def list_children(self, page_id: str) -> list:
        """List child pages of a given page"""
        url = f"{self.base_url}/rest/api/content/{page_id}/child/page"
        params = {"os_authType": "basic", "limit": 100}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            data = response.json()

            return [{
                "id": item["id"],
                "title": item["title"],
                "url": f"{self.base_url}/pages/viewpage.action?pageId={item['id']}"
            } for item in data.get("results", [])]

    async def get_spaces(self, limit: int = 100) -> list:
        """Get list of Confluence spaces"""
        url = f"{self.base_url}/rest/api/space"
        params = {"os_authType": "basic", "limit": limit}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=self.auth, params=params)
            response.raise_for_status()
            data = response.json()

            return [{
                "key": item["key"],
                "name": item["name"],
                "type": item.get("type", "global")
            } for item in data.get("results", [])]

    # ============ Table Operations ============

    def list_tables(self, html_content: str) -> list:
        """Parse HTML and return info about all tables"""
        tables = []
        table_pattern = r'<table[^>]*>(.*?)</table>'

        for idx, match in enumerate(re.finditer(table_pattern, html_content, re.DOTALL)):
            table_html = match.group(0)
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)

            if not rows:
                continue

            # Get header row
            header_row = []
            first_row = rows[0]
            header_cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', first_row, re.DOTALL)
            for cell in header_cells:
                cell_text = re.sub(r'<[^>]+>', '', cell).strip()
                header_row.append(cell_text)

            # Count columns and rows
            col_count = len(header_row) if header_row else 0
            row_count = len(rows)

            tables.append({
                "index": idx,
                "header_row": header_row,
                "row_count": row_count,
                "col_count": col_count,
                "preview": " | ".join(header_row[:5]) + ("..." if len(header_row) > 5 else "")
            })

        return tables

    def insert_table_column(self, html_content: str, table_index: int, column_position: int,
                            column_name: str, default_value: str = "") -> str:
        """Insert a new column into a table at the specified position"""
        tables = list(re.finditer(r'<table[^>]*>.*?</table>', html_content, re.DOTALL))

        if table_index >= len(tables):
            raise ValueError(f"Table index {table_index} out of range (total tables: {len(tables)})")

        table_match = tables[table_index]
        table_html = table_match.group(0)

        # Process each row
        def process_row(row_match):
            row_html = row_match.group(0)
            is_header = '<th' in row_html

            # Check for colspan in this row (skip complex header rows)
            if 'colspan' in row_html.lower():
                return row_html

            # Find all cells
            cells = list(re.finditer(r'<(t[hd])([^>]*)>(.*?)</\1>', row_html, re.DOTALL))

            if column_position > len(cells):
                return row_html

            # Create new cell
            tag = 'th' if is_header else 'td'
            value = column_name if is_header else default_value
            new_cell = f'<{tag}>{html.escape(value)}</{tag}>'

            # Insert at position
            if column_position == 0:
                # Insert at beginning
                first_cell = cells[0] if cells else None
                if first_cell:
                    return row_html[:first_cell.start()] + new_cell + row_html[first_cell.start():]
            else:
                # Insert after the cell at position-1
                if column_position <= len(cells):
                    prev_cell = cells[column_position - 1]
                    insert_pos = prev_cell.end()
                    return row_html[:insert_pos] + new_cell + row_html[insert_pos:]

            return row_html

        # Process all rows in the table
        new_table_html = re.sub(r'<tr[^>]*>.*?</tr>', process_row, table_html, flags=re.DOTALL)

        # Replace table in content
        return html_content[:table_match.start()] + new_table_html + html_content[table_match.end():]

    def delete_table_column(self, html_content: str, table_index: int, column_position: int) -> str:
        """Delete a column from a table at the specified position"""
        tables = list(re.finditer(r'<table[^>]*>.*?</table>', html_content, re.DOTALL))

        if table_index >= len(tables):
            raise ValueError(f"Table index {table_index} out of range (total tables: {len(tables)})")

        table_match = tables[table_index]
        table_html = table_match.group(0)

        # Process each row
        def process_row(row_match):
            row_html = row_match.group(0)

            # Check for colspan (skip complex header rows)
            if 'colspan' in row_html.lower():
                return row_html

            # Find all cells
            cells = list(re.finditer(r'<(t[hd])([^>]*)>(.*?)</\1>', row_html, re.DOTALL))

            if column_position >= len(cells):
                return row_html

            # Remove the cell at position
            cell_to_remove = cells[column_position]
            return row_html[:cell_to_remove.start()] + row_html[cell_to_remove.end():]

        # Process all rows
        new_table_html = re.sub(r'<tr[^>]*>.*?</tr>', process_row, table_html, flags=re.DOTALL)

        # Replace table in content
        return html_content[:table_match.start()] + new_table_html + html_content[table_match.end():]

    def update_table_cell(self, html_content: str, table_index: int, row_index: int,
                          column_index: int, content: str, append: bool = False) -> str:
        """Update a specific cell in a table

        Args:
            html_content: Page HTML content
            table_index: Table index (0-based)
            row_index: Row index (0=header row, 1=first data row)
            column_index: Column index (0-based)
            content: New content (text, HTML, Markdown, or [image:filename.png])
            append: If True, append to existing content; if False, replace

        Returns:
            Updated HTML content
        """
        tables = list(re.finditer(r'<table[^>]*>.*?</table>', html_content, re.DOTALL))

        if table_index >= len(tables):
            raise ValueError(f"表格索引 {table_index} 超出范围（共 {len(tables)} 个表格）")

        table_match = tables[table_index]
        table_html = table_match.group(0)

        # Find all rows
        rows = list(re.finditer(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL))

        if row_index >= len(rows):
            raise ValueError(f"行索引 {row_index} 超出范围（共 {len(rows)} 行）")

        row_match = rows[row_index]
        row_html = row_match.group(0)

        # Check for colspan/rowspan in this row
        if 'colspan' in row_html.lower() or 'rowspan' in row_html.lower():
            raise ValueError("该行包含合并单元格（colspan/rowspan），请使用 edit_confluence_page 直接编辑 HTML")

        # Find all cells in this row
        cells = list(re.finditer(r'<(t[hd])([^>]*)>(.*?)</\1>', row_html, re.DOTALL))

        if column_index >= len(cells):
            raise ValueError(f"列索引 {column_index} 超出范围（该行共 {len(cells)} 列）")

        cell_match = cells[column_index]
        tag = cell_match.group(1)  # 'th' or 'td'
        attrs = cell_match.group(2)  # preserve attributes like style
        old_content = cell_match.group(3)

        # Process content: handle [image:filename] syntax
        new_content = self._process_cell_content(content)

        # Append or replace
        if append:
            final_content = old_content + new_content
        else:
            final_content = new_content

        # Build new cell
        new_cell = f'<{tag}{attrs}>{final_content}</{tag}>'

        # Replace cell in row
        new_row_html = row_html[:cell_match.start()] + new_cell + row_html[cell_match.end():]

        # Replace row in table
        new_table_html = table_html[:row_match.start()] + new_row_html + table_html[row_match.end():]

        # Replace table in content
        return html_content[:table_match.start()] + new_table_html + html_content[table_match.end():]

    def _process_cell_content(self, content: str) -> str:
        """Process cell content, handling special syntax like [image:filename] and basic Markdown"""
        # Handle [image:filename.png] syntax first
        image_pattern = r'\[image:([^\]]+)\]'

        def replace_image(match):
            filename = match.group(1)
            return f'<ac:image><ri:attachment ri:filename="{html.escape(filename)}"/></ac:image>'

        processed = re.sub(image_pattern, replace_image, content)

        # Handle Markdown image syntax ![alt](filename) - works even inside HTML
        def replace_md_image(match):
            filename = match.group(2)
            # If it's just a filename (not a URL), treat as attachment
            if not filename.startswith('http'):
                return f'<ac:image><ri:attachment ri:filename="{html.escape(filename)}"/></ac:image>'
            return f'<img src="{html.escape(filename)}"/>'

        processed = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_md_image, processed)

        # Process inline Markdown formatting (bold, italic) even in HTML content
        # Bold: **text** or __text__
        processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', processed)
        processed = re.sub(r'__(.+?)__', r'<strong>\1</strong>', processed)

        # Italic: *text* (but not ** which is bold)
        processed = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', processed)

        # If content already looks like HTML (starts with <) and has been processed, return
        if processed.strip().startswith('<'):
            return processed

        # For non-HTML content, do full Markdown conversion (links, code, etc.)
        processed = self._markdown_to_html(processed)

        return processed

    def _markdown_to_html(self, text: str) -> str:
        """Convert basic Markdown syntax to HTML for Confluence"""
        # Images FIRST: ![alt](filename) - must come before links to avoid conflict
        def replace_md_image(match):
            filename = match.group(2)
            # If it's just a filename (not a URL), treat as attachment
            if not filename.startswith('http'):
                return f'<ac:image><ri:attachment ri:filename="{html.escape(filename)}"/></ac:image>'
            return f'<img src="{html.escape(filename)}"/>'

        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_md_image, text)

        # Bold: **text** or __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

        # Italic: *text* or _text_ (but not inside URLs or already processed)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

        # Inline code: `code`
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

        # Links: [text](url) - after images to avoid matching ![alt](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

        # Line breaks: \n to <br/> (but preserve existing <br> tags)
        # Don't convert if there's already HTML tags
        if '<' not in text or text.count('<br') > 0:
            text = text.replace('\n', '<br/>')

        return text

    def insert_table_row(self, html_content: str, table_index: int, row_position: int,
                         cell_values: list, is_header: bool = False) -> str:
        """Insert a new row into a table

        Args:
            html_content: Page HTML content
            table_index: Table index (0-based)
            row_position: Insert position (0=before header, 1=after header, ...)
            cell_values: List of cell values
            is_header: If True, create <th> cells; if False, create <td> cells

        Returns:
            Updated HTML content
        """
        tables = list(re.finditer(r'<table[^>]*>.*?</table>', html_content, re.DOTALL))

        if table_index >= len(tables):
            raise ValueError(f"表格索引 {table_index} 超出范围（共 {len(tables)} 个表格）")

        table_match = tables[table_index]
        table_html = table_match.group(0)

        # Find all rows
        rows = list(re.finditer(r'<tr[^>]*>.*?</tr>', table_html, re.DOTALL))

        if row_position > len(rows):
            raise ValueError(f"行位置 {row_position} 超出范围（可插入位置 0-{len(rows)}）")

        # Build new row
        tag = 'th' if is_header else 'td'
        cells_html = ''.join(f'<{tag}>{self._process_cell_content(str(v))}</{tag}>' for v in cell_values)
        new_row = f'<tr>{cells_html}</tr>'

        # Insert at position
        if row_position == 0:
            # Insert before first row
            if rows:
                insert_pos = rows[0].start()
            else:
                # Empty table - insert after <tbody> or <table>
                tbody_match = re.search(r'<tbody[^>]*>', table_html)
                if tbody_match:
                    insert_pos = tbody_match.end()
                else:
                    # Insert after <table...>
                    table_tag_match = re.match(r'<table[^>]*>', table_html)
                    insert_pos = table_tag_match.end() if table_tag_match else 0
        elif row_position >= len(rows):
            # Insert after last row
            insert_pos = rows[-1].end()
        else:
            # Insert after the row at position-1
            insert_pos = rows[row_position - 1].end()

        new_table_html = table_html[:insert_pos] + new_row + table_html[insert_pos:]

        # Replace table in content
        return html_content[:table_match.start()] + new_table_html + html_content[table_match.end():]

    def delete_table_row(self, html_content: str, table_index: int, row_index: int) -> str:
        """Delete a row from a table

        Args:
            html_content: Page HTML content
            table_index: Table index (0-based)
            row_index: Row index to delete (0=header row, 1=first data row)

        Returns:
            Updated HTML content
        """
        tables = list(re.finditer(r'<table[^>]*>.*?</table>', html_content, re.DOTALL))

        if table_index >= len(tables):
            raise ValueError(f"表格索引 {table_index} 超出范围（共 {len(tables)} 个表格）")

        table_match = tables[table_index]
        table_html = table_match.group(0)

        # Find all rows
        rows = list(re.finditer(r'<tr[^>]*>.*?</tr>', table_html, re.DOTALL))

        if row_index >= len(rows):
            raise ValueError(f"行索引 {row_index} 超出范围（共 {len(rows)} 行）")

        # Check for colspan/rowspan
        row_html = rows[row_index].group(0)
        if 'rowspan' in row_html.lower():
            raise ValueError("该行包含跨行单元格（rowspan），删除可能破坏表格结构，请使用 edit_confluence_page 直接编辑")

        # Remove the row
        row_match = rows[row_index]
        new_table_html = table_html[:row_match.start()] + table_html[row_match.end():]

        # Replace table in content
        return html_content[:table_match.start()] + new_table_html + html_content[table_match.end():]
