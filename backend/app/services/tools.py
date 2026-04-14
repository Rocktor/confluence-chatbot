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
            "name": "move_confluence_page",
            "description": "移动 Confluence 页面到新的父页面下。当用户要求移动页面、调整目录结构、把页面挪到另一个位置时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "要移动的页面 ID 或 URL"
                    },
                    "new_parent_id_or_url": {
                        "type": "string",
                        "description": "目标父页面 ID 或 URL（页面将移动到此页面下）"
                    }
                },
                "required": ["page_id_or_url", "new_parent_id_or_url"]
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
    {
        "type": "function",
        "function": {
            "name": "list_confluence_attachments",
            "description": "列出 Confluence 页面的所有附件。当用户想查看页面有哪些附件、或准备读取附件时使用。",
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
            "name": "read_confluence_attachment",
            "description": "读取 Confluence 页面附件的内容（仅支持文本文件）。支持按文件名或索引读取。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "页面 ID 或 URL"
                    },
                    "filename": {
                        "type": "string",
                        "description": "附件文件名（可选，与 attachment_index 二选一）"
                    },
                    "attachment_index": {
                        "type": "integer",
                        "description": "附件索引，从 0 开始（可选，与 filename 二选一）"
                    }
                },
                "required": ["page_id_or_url"]
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
    {
        "type": "function",
        "function": {
            "name": "update_table_cell",
            "description": "编辑 Confluence 页面表格中的指定单元格。支持文本、HTML 和图片插入。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id_or_url": {
                        "type": "string",
                        "description": "页面 ID 或 URL"
                    },
                    "table_index": {
                        "type": "integer",
                        "description": "表格索引，从 0 开始（先用 list_confluence_tables 查看）"
                    },
                    "row_index": {
                        "type": "integer",
                        "description": "行索引（0=表头，1=第一数据行，2=第二数据行...）"
                    },
                    "column_index": {
                        "type": "integer",
                        "description": "列索引，从 0 开始"
                    },
                    "content": {
                        "type": "string",
                        "description": "新内容。支持：普通文本、HTML、[image:filename.png] 插入图片"
                    },
                    "append": {
                        "type": "boolean",
                        "description": "是否追加到现有内容后面（默认 false 替换）"
                    }
                },
                "required": ["page_id_or_url", "table_index", "row_index", "column_index", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "insert_table_row",
            "description": "在 Confluence 页面表格中插入新行。",
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
                    "row_position": {
                        "type": "integer",
                        "description": "插入位置（1=表头后第一行，2=第二行...末尾可用表格行数）"
                    },
                    "cell_values": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "每列的值，如 [\"值1\", \"值2\", \"值3\"]。支持 [image:filename.png] 语法"
                    },
                    "is_header": {
                        "type": "boolean",
                        "description": "是否为表头行（默认 false 为数据行）"
                    }
                },
                "required": ["page_id_or_url", "table_index", "row_position", "cell_values"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_table_row",
            "description": "删除 Confluence 页面表格中的指定行。",
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
                    "row_index": {
                        "type": "integer",
                        "description": "要删除的行索引（0=表头，1=第一数据行...）"
                    }
                },
                "required": ["page_id_or_url", "table_index", "row_index"]
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
    },
    # ============ 图片查看工具 ============
    {
        "type": "function",
        "function": {
            "name": "view_confluence_image",
            "description": "查看 Confluence 页面中的一张附件图片。当用户问到页面图片内容、需要分析截图或图表时使用。每次只查看一张图片，如需查看多张请多次调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "页面 ID"
                    },
                    "filename": {
                        "type": "string",
                        "description": "图片文件名（从 read_confluence_page 返回的 images 列表中获取）"
                    }
                },
                "required": ["page_id", "filename"]
            }
        }
    },
    # ============ 审稿工具 ============
    {
        "type": "function",
        "function": {
            "name": "review_meeting_material",
            "description": "根据营销服会议材料审稿标准，对文档进行专业审稿。当用户要求审核、审稿、检查会议材料质量时使用。返回审稿标准和文档内容，由你生成完整审稿报告。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "要审核的文档内容（直接传入文本）。与 page_id_or_url 二选一。"
                    },
                    "page_id_or_url": {
                        "type": "string",
                        "description": "要审核的 Confluence 页面 ID 或 URL。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "review_experiment_retrospective",
            "description": "根据运营策略实验复盘审稿标准，对实验复盘文档进行专业审稿。当用户要求审核实验复盘、AB测试报告、实验方案时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "要审核的文档内容（直接传入文本）。与 page_id_or_url 二选一。"
                    },
                    "page_id_or_url": {
                        "type": "string",
                        "description": "要审核的 Confluence 页面 ID 或 URL。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "review_sla_contract",
            "description": "根据SLA合同审稿标准，对SLA合同进行专业审核。当用户要求审核SLA、服务协议、内部结算协议时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "要审核的文档内容（直接传入文本）。与 page_id_or_url 二选一。"
                    },
                    "page_id_or_url": {
                        "type": "string",
                        "description": "要审核的 Confluence 页面 ID 或 URL。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "review_meeting_submission",
            "description": "根据营销服会材料审核规范（Gate+Score模式），对议题材料进行10分制结构化评分。底线层4项硬门槛检查 + 上限层4项评级 + CEO判定模式风险预判，输出三态结论（通过/条件通过/不通过）。当用户要求审核上会材料、营销服会材料、周报议题时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "要审核的文档内容（直接传入文本）。与 page_id_or_url 二选一。"
                    },
                    "page_id_or_url": {
                        "type": "string",
                        "description": "要审核的 Confluence 页面 ID 或 URL。"
                    }
                },
                "required": []
            }
        }
    }
]

SYSTEM_PROMPT = """你是一个智能文档助手，可以帮助用户管理 Confluence 文档。

## 核心规则

1. 调用 read_confluence_page 后，必须向用户总结或回答问题，不能沉默
2. 如果内容太长，只总结关键要点
3. **图片上传必须两步完成**：上传附件后，必须再调用工具把图片插入到页面内容中！

## ⚠️ 图片上传的正确流程（最重要！）

当用户上传图片要插入 Confluence 页面时，**必须按顺序完成以下两步**：

**第1步：上传附件**
```
upload_attachment_to_confluence(page_id="123", file_url="/uploads/xxx.jpg")
→ 返回 {"success": true, "filename": "xxx.jpg"}
```

**第2步：插入图片到页面（必须执行！）**
上传成功后，**必须立即**调用以下工具之一把图片插入页面：
- 插入表格单元格：`update_table_cell(content="[image:xxx.jpg]")`
- 插入表格新行：`insert_table_row(cell_values=["[image:xxx.jpg]", "说明文字"])`
- 插入正文：`edit_confluence_page(new_content="<ac:image><ri:attachment ri:filename=\"xxx.jpg\"/></ac:image>")`

**⚠️ 注意**：
1. 表格操作使用 `[image:filename]` 语法，系统会自动转换
2. Markdown 格式（如 `**粗体**`）会自动转换为 HTML
3. 只执行第1步不会在页面显示图片！必须执行第2步！

## 可用工具

### 页面操作
- read_confluence_page: 读取页面（返回 Markdown 和原始 HTML）
- edit_confluence_page: 精确编辑（在原始 HTML 中替换指定内容）⬅️ 推荐用于修改
- insert_content_to_confluence_page: 在页面开头或结尾插入内容（保留原有内容）
- update_confluence_page: 完全替换页面内容（会覆盖原有内容！）
- create_confluence_page: 创建新页面
- search_confluence: 搜索页面
- upload_attachment_to_confluence: 上传附件到页面
- view_confluence_image: 查看页面中的附件图片（按需调用，用于分析图片内容）

### 表格操作 ⭐
- list_confluence_tables: 列出页面中的所有表格信息
- update_table_cell: 编辑指定单元格（支持文本、HTML、图片）⬅️ 核心功能
- insert_table_row: 在表格中插入新行
- delete_table_row: 删除表格中的指定行
- insert_table_column: 在表格中插入新列
- delete_table_column: 删除表格中的指定列

### 导航工具
- list_children_pages: 列出子页面
- get_confluence_spaces: 获取空间列表

### 审稿工具
- review_meeting_material: 审核会议材料质量（审稿评分）
- review_experiment_retrospective: 审核实验复盘材料（五条红线 + 6维度评分）
- review_sla_contract: 审核SLA合同（八大维度风险审核）
- review_meeting_submission: 审核上会材料（Gate底线层 + Score上限层 + CEO判定模式，10分制评分）

## 编辑策略（重要）

### ⛔ 绝对禁止的行为
- **edit_confluence_page 失败后，绝对不要使用 update_confluence_page 重写整个页面！**
- 如果 edit_confluence_page 返回"未找到要替换的内容"，应该：
  1. 重新调用 read_confluence_page 获取最新 HTML
  2. 从 html 字段中更精确地复制要替换的 HTML 片段
  3. 如果是表格内容，改用 update_table_cell 工具
  4. 绝不能因为精确编辑失败就改用全量替换

### 表格内容修改（最常见场景）
- **修改表格单元格内容时，必须优先使用 update_table_cell**
- 操作步骤：先 list_confluence_tables → 确认索引 → update_table_cell
- 只有当 update_table_cell 因 colspan/rowspan 失败时，才用 edit_confluence_page 直接编辑 HTML

### 优先使用 edit_confluence_page（精确编辑）
- 修改正文段落、标题等非表格内容
- 需要保留原有格式和图片
- 从 read_confluence_page 返回的 `html` 字段中找到要修改的 HTML 片段

### 使用 insert_content_to_confluence_page
- 在开头添加总结、在结尾添加内容

### 仅在必要时使用 update_confluence_page
- 仅当用户明确要求"重写整个页面"或"替换全部内容"时
- **绝不能作为 edit_confluence_page 失败的后备方案！**

## 表格操作策略

1. 先调用 list_confluence_tables 查看页面有哪些表格
2. 确认表格索引（从 0 开始）、行索引、列索引后再操作
3. 行索引：0=表头行，1=第一数据行，2=第二数据行...
4. 列索引：从 0 开始

### 单元格编辑（update_table_cell）
- 修改某个单元格内容：指定 table_index、row_index、column_index
- 插入图片：content 使用 [image:filename.png] 语法（先上传附件！）
- 追加内容：设置 append=true

### 行操作
- insert_table_row: 在指定位置插入新行，cell_values 提供每列的值
- delete_table_row: 删除指定行

### 注意事项
- 遇到 colspan/rowspan（合并单元格）会返回错误，建议用 edit_confluence_page 直接编辑 HTML

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
4. 系统会精确替换，保留其他所有内容

## 图片识别能力

读取 Confluence 页面时，系统会自动下载页面中的附件图片（最多 5 张）并展示给你。
- 直接描述和分析你看到的图片内容（文字、图表、截图等）
- 告诉用户你看了哪些图片，以及每张图片的内容
- 如果页面图片超过 5 张，可使用 view_confluence_image 工具查看未自动下载的图片
- 结合图片和文字内容进行综合分析

## 语言要求

请始终使用中文回复用户。不要在回复正文中输出你的内部推理过程。"""


REVIEW_STANDARD = """# 营销服会议材料审稿标准 v1.0

## 一、四条红线（核心原则）

### 红线1：可读性第一
- 任何不具备业务背景的高管，5分钟内能读完并理解核心结论
- 禁止出现未解释的专业缩写
- 句子长度不超过 40 字

### 红线2：结论优先
- 每页开头必须有明确结论/观点
- 禁止"数据罗列不下结论"
- 结论必须可证伪（不能是正确的废话）

### 红线3：观点可追责
- 每个结论必须有数据或事实支撑
- 数据来源必须标注
- 禁止"大家觉得""业界普遍认为"等模糊归因

### 红线4：直接支撑决策
- 材料必须服务于具体决策议题
- 每一页都要回答"所以呢？"
- 提供明确的行动建议或选项

## 二、文档结构要求（5 屏原则）

理想的会议材料不超过 5 个核心屏幕/页面：

| 屏幕 | 内容 | 要求 |
|------|------|------|
| 1. 决策屏 | 要做什么决策？推荐方案是什么？ | 一句话结论 + 关键数字 |
| 2. 证据屏 | 为什么推荐这个方案？ | 数据图表 + 逻辑推导 |
| 3. 对比屏 | 还有哪些备选方案？ | 对比表格（维度一致） |
| 4. 计划屏 | 如何执行？时间表？ | 里程碑 + 责任人 |
| 5. 风险屏 | 主要风险及应对措施 | 风险矩阵或列表 |

## 三、一票否决项（6 项，任一命中即不通过）

1. **无结论/结论模糊** - 材料读完不知道要决策什么
2. **数据无来源** - 引用数据未标注出处
3. **逻辑断裂** - 结论与论据之间缺乏推导过程
4. **只有一个方案** - 未提供备选方案进行对比
5. **无行动建议** - 分析了问题但不给出下一步
6. **篇幅失控** - 核心内容超过 10 页/屏

## 四、评分维度（5 维度 x 0-2 分，满分 10 分）

| 维度 | 0 分 | 1 分 | 2 分 |
|------|------|------|------|
| 结论清晰度 | 无结论或结论模糊 | 有结论但不够锐利 | 结论明确、可执行 |
| 数据支撑度 | 无数据或数据不可信 | 有数据但不充分 | 数据充分且有来源 |
| 结构完整度 | 缺少关键模块 | 结构基本完整 | 5 屏齐全、逻辑清晰 |
| 可读性 | 读不懂/太长 | 基本能读但费力 | 5 分钟内读完理解 |
| 决策支撑度 | 看完不知道怎么决策 | 能决策但信息不足 | 直接支撑决策 |

## 五、评审者注意事项

- 区分"材料质量"与"业务方向" -- 本标准只评审材料质量
- 用建设性语气提出修改意见
- 对每个扣分项给出具体的改进建议"""


REVIEW_OUTPUT_FORMAT = """请按照以下格式输出审稿结果：

---

## 会议材料审稿报告

### 1. 总体评价
[一句话总结材料质量，是否通过审稿]

### 2. 一票否决项检查
| 检查项 | 结果 | 说明 |
|--------|------|------|
| 无结论/结论模糊 | 通过 / 不通过 | [具体说明] |
| 数据无来源 | 通过 / 不通过 | [具体说明] |
| 逻辑断裂 | 通过 / 不通过 | [具体说明] |
| 只有一个方案 | 通过 / 不通过 | [具体说明] |
| 无行动建议 | 通过 / 不通过 | [具体说明] |
| 篇幅失控 | 通过 / 不通过 | [具体说明] |

**一票否决结果**：[全部通过 / 存在不通过项，材料需修改]

### 3. 评分明细
| 维度 | 得分 | 评价 |
|------|------|------|
| 结论清晰度 | X/2 | [具体评价] |
| 数据支撑度 | X/2 | [具体评价] |
| 结构完整度 | X/2 | [具体评价] |
| 可读性 | X/2 | [具体评价] |
| 决策支撑度 | X/2 | [具体评价] |
| **总分** | **X/10** | |

### 4. 文档结构分析（5 屏原则）
[对照 5 屏要求，分析材料是否覆盖了每个关键屏幕]

### 5. 具体修改建议
[按优先级列出 3-5 条最重要的修改建议，每条说明原因和改进方向]

### 6. 亮点
[列出材料做得好的 1-2 个方面]

---"""


# ============ 实验复盘审稿标准 ============
EXPERIMENT_REVIEW_STANDARD = """# 运策实验复盘审稿标准 v1.0

## 一、五条红线（核心原则）

### 红线1：可读性第一
- 任何不具备业务背景的人，10分钟内能读完并理解核心结论
- 禁止出现未解释的专业缩写
- 句子长度不超过 40 字

### 红线2：结论先行
- 每屏开头必须有明确结论/观点
- 禁止"数据罗列不下结论"

### 红线3：数据可追溯
- 每个结论必须有数据支撑
- 数据来源/取数口径必须标注

### 红线4：实验可复现
- 实验设计必须包含分组逻辑、样本量、实验周期
- 他人能据此复现实验

### 红线5：行动驱动
- 材料必须回答"所以呢？下一步做什么？"

## 二、文档结构要求（6屏原则）

| 屏幕 | 内容 | 要求 |
|------|------|------|
| 1. 背景屏 | 实验背景与假设 | 一句话假设 + 业务目标 |
| 2. 设计屏 | 实验方案设计 | 分组/样本/周期/指标定义 |
| 3. 结果屏 | 核心实验结果 | 关键指标对比 + 统计显著性 |
| 4. 分析屏 | 深入分析与归因 | 分维度/分群分析 |
| 5. 结论屏 | 结论与决策建议 | 明确推荐方案 + 推广计划 |
| 6. 附录屏 | 补充数据与说明 | 详细数据表/注意事项 |

## 三、一票否决项（8项，任一命中即不通过）

1. **无假设/假设模糊** - 不清楚在验证什么
2. **实验设计缺失** - 无分组逻辑或样本量说明
3. **数据无来源** - 引用数据未标注出处/取数口径
4. **无统计检验** - 结果未做显著性检验或置信区间
5. **逻辑断裂** - 结论与数据之间缺乏推导
6. **只有结果无归因** - 只说"涨了/跌了"不分析原因
7. **无行动建议** - 复盘了但不给下一步
8. **篇幅失控** - 核心内容超过 12 页/屏

## 四、评分维度（6维度 x 0-2分，满分12分）

| 维度 | 0分 | 1分 | 2分 |
|------|------|------|------|
| 假设清晰度 | 无假设或假设模糊 | 有假设但不够具体 | 假设明确、可证伪 |
| 实验设计 | 设计缺失/有重大漏洞 | 设计基本合理 | 设计严谨、可复现 |
| 数据分析 | 无分析或分析粗糙 | 有分析但不深入 | 多维度深入分析 |
| 结论可信度 | 结论无支撑 | 有支撑但不充分 | 数据充分+统计检验 |
| 可读性 | 读不懂/太长 | 基本能读但费力 | 10分钟内读完理解 |
| 行动驱动 | 无下一步 | 有建议但不具体 | 明确推广/迭代计划 |

## 五、评审者注意事项

- 区分"材料质量"与"实验结果好坏" -- 本标准只评审复盘材料的质量，不评判实验本身成败
- 失败的实验如果复盘写得好，同样可以高分通过
- 重点关注因果归因的严谨性 -- 这是实验复盘区别于普通数据分析的核心
- 鼓励诚实汇报失败 -- 对"实验失败但清晰归因了原因"的材料，应在亮点中肯定
- 用建设性语气提出修改意见
- 对每个扣分项给出具体的改进建议"""


EXPERIMENT_REVIEW_OUTPUT_FORMAT = """请按照以下格式输出审稿结果：

---

## 实验复盘审稿报告

### 1. 总体评价
[一句话总结复盘质量，是否通过审稿]

### 2. 一票否决项检查
| 检查项 | 结果 | 说明 |
|--------|------|------|
| 无假设/假设模糊 | 通过/不通过 | [具体说明] |
| 实验设计缺失 | 通过/不通过 | [具体说明] |
| 数据无来源 | 通过/不通过 | [具体说明] |
| 无统计检验 | 通过/不通过 | [具体说明] |
| 逻辑断裂 | 通过/不通过 | [具体说明] |
| 只有结果无归因 | 通过/不通过 | [具体说明] |
| 无行动建议 | 通过/不通过 | [具体说明] |
| 篇幅失控 | 通过/不通过 | [具体说明] |

**一票否决结果**：[全部通过 / 存在不通过项，材料需修改]

### 3. 评分明细
| 维度 | 得分 | 评价 |
|------|------|------|
| 假设清晰度 | X/2 | [具体评价] |
| 实验设计 | X/2 | [具体评价] |
| 数据分析 | X/2 | [具体评价] |
| 结论可信度 | X/2 | [具体评价] |
| 可读性 | X/2 | [具体评价] |
| 行动驱动 | X/2 | [具体评价] |
| **总分** | **X/12** | |

### 4. 文档结构分析（6屏原则）
[对照6屏要求，分析覆盖情况]

### 5. 具体修改建议
[按优先级列出3-5条修改建议]

### 6. 亮点
[材料做得好的1-2个方面]

---"""


# ============ SLA合同审稿标准 ============
SLA_REVIEW_STANDARD = """# SLA合同审稿标准 v1.0

## 一、八大审核维度

### 维度1：结算逻辑审核
- 结算公式是否明确、无歧义
- 计费周期、计费单位是否清晰
- 是否有结算示例
- 异常情况的结算处理规则

### 维度2：风险对称性
- 甲乙双方的违约责任是否对等
- 赔偿上限/下限是否合理
- 不可抗力条款是否公平

### 维度3：可量化目标
- SLA指标是否有明确数值定义
- 达标/未达标的判定标准是否清晰
- 监测方式和数据来源是否约定

### 维度4：交付条款
- 交付物清单是否完整
- 验收标准是否明确
- 交付时间节点是否合理

### 维度5：退出机制
- 合同终止条件是否明确
- 提前终止的违约金计算
- 数据交接和过渡期安排

### 维度6：争议解决
- 争议解决方式是否约定（仲裁/诉讼）
- 管辖地约定
- 争议期间的服务持续性

### 维度7：条款一致性
- 正文与附件的一致性
- 术语定义的一致性
- 金额/日期等数字的一致性

### 维度8：类型专项检查
根据合同类型进行专项审核：

#### 人力买断型
- 人员资质要求是否明确
- 替换机制和审批流程
- 工作量确认方式

#### 增量价值分成型
- 基准值的确定方式
- 增量的计算口径
- 分成比例和结算周期

#### 计件型
- 计件单价和单位定义
- 质量标准和抽检机制
- 最低/最高量的约束

#### 里程碑型
- 里程碑节点和交付物
- 各节点付款比例
- 延期处理机制"""


SLA_REVIEW_OUTPUT_FORMAT = """请按照以下格式输出审稿结果：

---

## SLA合同审稿报告

### 1. 合同概况
[合同类型、甲乙方、合同期限、总金额等基本信息]

### 2. 八大维度审核

#### 2.1 结算逻辑
| 检查项 | 结果 | 说明 |
|--------|------|------|
| 结算公式明确性 | 通过/风险/缺失 | [具体说明] |
| 计费周期清晰度 | 通过/风险/缺失 | [具体说明] |
| 异常处理规则 | 通过/风险/缺失 | [具体说明] |

#### 2.2 风险对称性
| 检查项 | 结果 | 说明 |
|--------|------|------|
| 违约责任对等性 | 通过/风险/缺失 | [具体说明] |
| 赔偿上限合理性 | 通过/风险/缺失 | [具体说明] |

#### 2.3 可量化目标
| 检查项 | 结果 | 说明 |
|--------|------|------|
| SLA指标数值化 | 通过/风险/缺失 | [具体说明] |
| 达标判定标准 | 通过/风险/缺失 | [具体说明] |

#### 2.4 交付条款
[交付条款审核结果]

#### 2.5 退出机制
[退出机制审核结果]

#### 2.6 争议解决
[争议解决审核结果]

#### 2.7 条款一致性
[条款一致性审核结果]

#### 2.8 类型专项检查
[根据合同类型的专项审核结果]

### 3. 风险评级
| 风险等级 | 数量 | 说明 |
|----------|------|------|
| 高风险 | X项 | [概述] |
| 中风险 | X项 | [概述] |
| 低风险 | X项 | [概述] |

### 4. 重点修改建议
[按优先级列出3-5条最重要的修改建议]

### 5. 合同亮点
[合同条款设计较好的1-2个方面]

---"""


# ============ 上会材料审核标准（基于 marketing-review skill v2.2.0） ============
MEETING_SUBMISSION_REVIEW_STANDARD = """# 营销服会材料审核规范（Gate + Score 模式）

## 审核标准版本：marketing-review skill v2.2.0
## 评分标准：10分满分制

---

## 1. 审核流程

对用户提供的 Confluence 议题材料，按以下流程逐项审核：
1. 底线层检查（4项，全部必须通过，否则直接判定"不通过"）
2. 底线层全部通过后 → 上限层检查（4项，影响评级）
3. 结合 CEO 判定模式预判风险点
4. 生成三态结论 + 10分制评分 + 质量等级

---

## 2. 底线层（Gate，全部必须通过，否则驳回）

### 2.1 三层结构完整（2分）
材料必须包含以下三层，各缺一层扣0.7分：
- **事实层**：当周关键数字 + 横向对比（vs上周/目标/竞品）
- **洞察层**：驱动因素分析（回答"为什么"，不是简单罗列事实）
- **行动层**：明确下一步行动 + 责任人姓名 + 完成日期

### 2.2 复盘三要素（1.5分，含问题/异常时适用）
当材料涉及问题、异常、失败时，必须包含以下三要素，各缺一项扣0.5分：
- **根因**：追到第三层（不能停留在表面原因）
- **责任人**：具体人名（不是部门名称）
- **系统性改善方案**：机制性解决方案，而非一次性补救

如材料无问题/异常，此项标记"不适用"，不扣分。

### 2.3 计划格式（1.5分）
每条 Action/计划必须包含：
- **Owner（责任人）**：缺失扣0.75分
- **DDL（截止日期）**：缺失扣0.75分

### 2.4 指标口径（1分）
自定义指标（非行业通用指标）必须定义统计口径。无口径定义扣1分。
通用指标（如 DAU、GMV）不要求额外定义口径。

---

## 3. 上限层（Score，影响评级，每项1分）

### 3.1 归因比例量化（1分）
洞察分析是否量化了归因比例（如"A因素贡献60%，B因素贡献30%"），而非模糊描述（如"主要由于..."）。

### 3.2 行动建议量化预期（1分）
行动计划是否包含量化预期效果（如"预计提升X%""节省X万元"），而非仅描述动作。

### 3.3 复盘方案系统性（1分）
复盘的改善方案是否为机制性/系统性方案（如流程优化、工具建设、制度完善），而非一次性补救措施。
如无复盘内容，此项标记"不适用"，不扣分。

### 3.4 图表规范（1分）
图表是否满足以下规范：
- 坐标轴标注清晰、从0开始
- 有基准线/目标线对比
- 数据标注完整

---

## 4. CEO判定模式（风险预判）

### 4.1 驳回触发器（19条，任一触发即标注风险）
1. 只有数字没有洞察，"罗列不是分析"
2. 归因模糊，"主要由于"但无比例量化
3. 行动计划无Owner或DDL，"谁来做？什么时候做完？"
4. 问题复盘停在表面，"根因没追到位"
5. 改善方案是一次性补救而非系统性方案
6. 结论淹没在过程描述中，"结论先行"
7. 自定义指标无口径定义
8. 数据来源不可追溯
9. 图表坐标轴不从0开始，造成视觉误导
10. 汇报"做了什么"而非"做好了什么"
11. 跨部门议题未体现协作共识
12. 风险评估缺失或流于形式
13. 请示类议题只有一个方案
14. ROI测算缺失或不可信
15. 完成事项无完成依据
16. 延期Action无延期原因和新计划
17. 颜色使用不符合规范（红好绿差蓝重点）
18. 正文超过1000字，"说不清楚说明没想清楚"
19. 附录缺失或链接无效

### 4.2 通过信号（12条，匹配越多评价越高）
1. 事实层数据扎实，横向对比充分
2. 洞察层归因量化、逻辑清晰
3. 行动层每条有Owner+DDL+量化预期
4. 复盘追到系统性根因并提出机制性方案
5. 结论先行，表达简洁准确
6. 图表规范、数据标注完整
7. 风险评估系统全面，应急预案具体
8. 请示类提供多方案对比，建议方案理由充分
9. 与公司战略（AI化、国际化等）对齐
10. 体现"成就客户、专业求真"价值观
11. 跨部门协作充分、共识清晰
12. 数据来源可追溯、口径定义清晰

---

## 5. 判定规则

| 条件 | 结论 | 质量等级 | 含义 |
|------|------|----------|------|
| 底线层4/4全过 + 上限层≥3/4达标 | **通过** | 🟢绿 | 可直接上会 |
| 底线层4/4全过 + 上限层<3/4 | **条件通过** | 🟡黄 | 修改上限层短板后可上会 |
| 底线层任一项未过 | **不通过** | 🔴红 | 驳回重写，底线层补齐后重新提交 |

**核心逻辑**：底线层是门槛，全部通过才有资格进入上限层评级。底线层有任何一项不过即判定不通过。

---

## 6. 10分制评分标准

| 维度 | 分值 | 评分规则 |
|------|------|----------|
| 底线层-三层结构 | 2分 | 事实层/洞察层/行动层各缺一层扣0.7分 |
| 底线层-复盘三要素 | 1.5分 | 根因/责任人/系统性方案各缺一项扣0.5分（不适用则满分） |
| 底线层-计划格式 | 1.5分 | 缺Owner扣0.75分，缺DDL扣0.75分 |
| 底线层-指标口径 | 1分 | 自定义指标无口径定义扣1分 |
| 上限层-归因比例量化 | 1分 | 洞察模糊无比例扣1分 |
| 上限层-行动量化预期 | 1分 | 无量化预期扣1分 |
| 上限层-复盘系统性 | 1分 | 一次性补救非机制性扣1分（不适用则满分） |
| 上限层-图表规范 | 1分 | 坐标轴/标注/基准缺失扣1分 |
| **合计** | **10分** | |

"""


MEETING_SUBMISSION_REVIEW_OUTPUT_FORMAT = """请严格按照以下固定格式输出审核结果：

---

## 议题严格复审

| 项目 | 内容 |
|------|------|
| 汇报人 | [从材料中识别] |
| 结论 | 通过/条件通过/不通过 |
| 评分 | X.X/10 |
| 底线层 | X/4通过 |
| 上限层 | X/4通过 |
| 质量等级 | 🟢绿/🟡黄/🔴红 |

---

### 一、底线层检查（Gate）

#### 1. 三层结构完整 — 通过/部分通过/未通过（X/2分）
- **事实层**：[检查结果，是否有当周数字+横向对比]
- **洞察层**：[检查结果，是否有驱动因素分析，回答"为什么"]
- **行动层**：[检查结果，是否有明确下一步+人名+日期]

#### 2. 复盘三要素 — 通过/部分通过/未通过/不适用（X/1.5分）
- **根因**：[检查结果，是否追到第三层]
- **责任人**：[检查结果，是否为具体人名]
- **系统性改善方案**：[检查结果，是否为机制性方案]

#### 3. 计划格式 — 通过/未通过（X/1.5分）
- **Owner**：[列出每条Action的Owner情况]
- **DDL**：[列出每条Action的DDL情况]

#### 4. 指标口径 — 通过/未通过（X/1分）
- [列出自定义指标及其口径定义情况]

---

### 二、上限层检查（Score）

#### 1. 归因比例量化 — 通过/未通过（X/1分）
[是否有量化归因比例，举例说明]

#### 2. 行动建议量化预期 — 通过/未通过（X/1分）
[是否有量化预期效果，举例说明]

#### 3. 复盘方案系统性 — 通过/未通过/不适用（X/1分）
[方案是否为机制性/系统性方案，举例说明]

#### 4. 图表规范 — 通过/未通过（X/1分）
[坐标轴/标注/基准线情况]

---

### 三、CEO驳回风险点
[列出触发了哪些CEO驳回触发器（编号+内容），引用具体材料内容]

### 四、通过信号
[列出匹配了哪些CEO通过信号（编号+内容），引用具体材料内容]

### 五、评分明细

| 维度 | 满分 | 得分 | 扣分原因 |
|------|------|------|----------|
| 三层结构 | 2 | X | [原因或"满分"] |
| 复盘三要素 | 1.5 | X | [原因或"满分"或"不适用"] |
| 计划格式 | 1.5 | X | [原因或"满分"] |
| 指标口径 | 1 | X | [原因或"满分"] |
| 归因比例量化 | 1 | X | [原因或"满分"] |
| 行动量化预期 | 1 | X | [原因或"满分"] |
| 复盘系统性 | 1 | X | [原因或"满分"或"不适用"] |
| 图表规范 | 1 | X | [原因或"满分"] |
| **合计** | **10** | **X.X** | |

### 六、修改建议
[按优先级编号列出具体可执行的修改建议，每条包含：]
1. **[问题]**：[具体描述] → **建议**：[如何修改]
2. ...

### 七、亮点
[列出材料做得好的1-2个方面]

---"""
