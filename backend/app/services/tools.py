# Confluence AI Agent Tools Definition

CONFLUENCE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_confluence_page",
            "description": "读取 Confluence 页面内容。当用户发送 Confluence 链接、想要查看、分析或引用某个文档时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "页面 ID 或完整 URL（如 https://docs.xxx.com/pages/viewpage.action?pageId=123）"
                    }
                },
                "required": ["page_id_or_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "insert_content_to_confluence_page",
            "description": "在 Confluence 页面开头或结尾插入新内容，完全保留原有内容、格式和图片。当用户要求添加总结、添加章节、在开头/结尾加内容时优先使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "要更新的页面 ID 或 URL"
                    },
                    "content": {
                        "type": "string",
                        "description": "要插入的内容（Markdown 格式）"
                    },
                    "position": {
                        "type": "string",
                        "enum": ["prepend", "append"],
                        "description": "插入位置：prepend=开头，append=结尾"
                    }
                },
                "required": ["page_id_or_url", "content", "position"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_confluence_page",
            "description": "精确编辑 Confluence 页面。在原始 HTML 中查找并替换指定内容，保留其他所有格式和图片。当用户要求修改某一段、某个标题、某个表格时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "页面 ID 或 URL"
                    },
                    "old_content": {
                        "type": "string",
                        "description": "要替换的原始内容（HTML 片段，从 read_confluence_page 返回的 html 字段中复制）"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "替换后的新内容（HTML 格式，或 Markdown 格式会自动转换）"
                    }
                },
                "required": ["page_id_or_url", "old_content", "new_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_confluence_page",
            "description": "完全替换 Confluence 页面内容。警告：会覆盖原有内容！仅当用户明确要求重写整个页面时使用。如果只是添加内容，请使用 insert_content_to_confluence_page。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "要更新的页面 ID 或 URL"
                    },
                    "content": {
                        "type": "string",
                        "description": "新的页面内容（Markdown 格式）"
                    },
                    "title": {
                        "type": "string",
                        "description": "新标题（可选，不填则保持原标题）"
                    }
                },
                "required": ["page_id_or_url", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_confluence_page",
            "description": "创建新的 Confluence 页面。当用户要求创建新文档时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "页面标题"
                    },
                    "content": {
                        "type": "string",
                        "description": "页面内容（Markdown 格式）"
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "父页面 ID（放在哪个目录下）"
                    },
                    "space_key": {
                        "type": "string",
                        "description": "空间 Key（如 cpb）"
                    }
                },
                "required": ["title", "content", "parent_id", "space_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_confluence",
            "description": "搜索 Confluence 页面。当用户想要查找文档时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "space_key": {
                        "type": "string",
                        "description": "限定搜索的空间（可选）"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "upload_attachment_to_confluence",
            "description": "上传附件（图片或文件）到 Confluence 页面。当用户上传了图片并要求添加到某个页面时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "目标页面 ID"
                    },
                    "file_url": {
                        "type": "string",
                        "description": "要上传的文件 URL（来自聊天上传，如 /uploads/xxx/file.jpg）"
                    }
                },
                "required": ["page_id", "file_url"]
            }
        }
    },
    # ============ 表格操作工具 ============
    {
        "type": "function",
        "function": {
            "name": "list_confluence_tables",
            "description": "列出 Confluence 页面中的所有表格信息。当用户想要了解页面有哪些表格、或者准备操作表格时先调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "页面 ID 或 URL"
                    }
                },
                "required": ["page_id_or_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "insert_table_column",
            "description": "在 Confluence 页面的表格中插入新列。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "页面 ID 或 URL"
                    },
                    "table_index": {
                        "type": "integer",
                        "description": "表格索引，从 0 开始（先用 list_confluence_tables 查看有哪些表格）"
                    },
                    "column_position": {
                        "type": "integer",
                        "description": "插入位置，从 0 开始（在该位置之前插入）"
                    },
                    "column_name": {
                        "type": "string",
                        "description": "新列的表头名称"
                    },
                    "default_value": {
                        "type": "string",
                        "description": "数据行的默认值（可选，默认为空）"
                    }
                },
                "required": ["page_id_or_url", "table_index", "column_position", "column_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_table_column",
            "description": "删除 Confluence 页面表格中的指定列。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "页面 ID 或 URL"
                    },
                    "table_index": {
                        "type": "integer",
                        "description": "表格索引，从 0 开始"
                    },
                    "column_position": {
                        "type": "integer",
                        "description": "要删除的列位置，从 0 开始"
                    }
                },
                "required": ["page_id_or_url", "table_index", "column_position"]
            }
        }
    },
    # ============ 导航工具 ============
    {
        "type": "function",
        "function": {
            "name": "list_children_pages",
            "description": "列出 Confluence 页面的所有子页面。当用户想要查看某个页面下有哪些子页面时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "父页面 ID 或 URL"
                    }
                },
                "required": ["page_id_or_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_confluence_spaces",
            "description": "获取 Confluence 空间列表。当用户想要查看有哪些空间、或者需要 space_key 时使用。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

SYSTEM_PROMPT = """你是一个智能文档助手，可以帮助用户管理 Confluence 文档。

## 核心规则

1. 调用 read_confluence_page 后，必须向用户总结或回答问题，不能沉默
2. 不要连续多次调用同一个工具
3. 如果内容太长，只总结关键要点

## 可用工具

### 页面操作
- read_confluence_page: 读取页面（返回 Markdown 和原始 HTML）
- edit_confluence_page: 精确编辑（在原始 HTML 中替换指定内容）⬅️ 推荐用于修改
- insert_content_to_confluence_page: 在页面开头或结尾插入内容（保留原有内容）
- update_confluence_page: 完全替换页面内容（会覆盖原有内容！）
- create_confluence_page: 创建新页面
- search_confluence: 搜索页面
- upload_attachment_to_confluence: 上传附件到页面

### 表格操作 ⭐
- list_confluence_tables: 列出页面中的所有表格信息
- insert_table_column: 在表格中插入新列
- delete_table_column: 删除表格中的指定列

### 导航工具
- list_children_pages: 列出子页面
- get_confluence_spaces: 获取空间列表

## 编辑策略（重要）

### 优先使用 edit_confluence_page（精确编辑）
- 修改某一段、某个标题、某个表格
- 需要保留原有格式和图片
- 从 read_confluence_page 返回的 `html` 字段中找到要修改的 HTML 片段

### 使用 insert_content_to_confluence_page
- 在开头添加总结
- 在结尾添加内容

### 仅在必要时使用 update_confluence_page
- 用户明确要求重写整个页面
- 原有内容不需要保留

## 表格操作策略

1. 先调用 list_confluence_tables 查看页面有哪些表格
2. 确认表格索引（从 0 开始）和列位置后再操作
3. 插入/删除列会自动处理跨列标题行

## Markdown 格式规范（重要）

生成 Markdown 内容时，必须遵循紧凑格式：
- 标题下面不要加空行，直接接正文
- 列表项之间不要加空行
- 段落之间最多一个空行
- 不要在内容开头或结尾加多余空行

错误示例（有多余空行）：
```
### 标题

- 项目1

- 项目2
```

正确示例（紧凑格式）：
```
### 标题
- 项目1
- 项目2
```

## 精确编辑示例

1. 读取页面后，查看返回的 `html` 字段
2. 找到要修改的 HTML 片段作为 `old_content`
3. 提供新的内容作为 `new_content`（可以是 HTML 或 Markdown）
4. 系统会精确替换，保留其他所有内容"""
