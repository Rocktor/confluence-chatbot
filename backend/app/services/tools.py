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
            "description": "根据营销服会上会材料审核规范，对上会材料进行结构化审核。检查四部分结构（审核意见、待办、正文、附录）、格式合规性、内容质量及CEO-1视角审核要点。当用户要求审核上会材料、周报材料时使用。",
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
- review_meeting_submission: 审核上会材料（四部分结构 + 格式合规 + CEO-1视角）

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


# ============ 上会材料审核标准 ============
MEETING_SUBMISSION_REVIEW_STANDARD = """# 营销服会上会材料审核规范

## 1. 目的
本规范旨在统一营销服会上会材料的格式与内容标准，确保材料结构清晰、数据可靠、待办可追踪、逻辑严谨、可执行性强，从而提升会议决策效率与质量。所有提交营销服会评审的周报及议题材料均须遵循本规范。

## 2. 适用范围
本规范适用于所有提交至营销服会的**周报类材料**，以及采用"审核意见→待办→正文→附录"结构的其他上会材料。

## 3. 材料标准结构
上会材料必须严格按照以下四部分顺序组织：
- **第一部分：审核意见**（含作者、Peer-review人、Peer-review意见）
- **第二部分：上周待办情况**（Action追踪）
- **第三部分：正文**（议题核心内容，字数≤1000字，图片≤5张）
- **第四部分：附录**（详细数据、报表、参考资料等，通过CF链接或附件提供）

## 4. 各部分详细要求及审核清单

### 4.1 第一部分：审核意见
| 审核项 | 硬性要求 | 检查方式 |
|--------|----------|----------|
| 作者 | 必须明确列出作者姓名（具体到人，不得只写部门） | 检查是否存在"作者"字段且内容为非空人名 |
| Peer-review人 | 必须明确列出至少一位Peer-review人姓名 | 检查是否存在"Peer-review人"字段且非空 |
| Peer-review意见 | 必须包含有效性评价（有效/无效/有条件通过）及评语 | 检查评语文本是否非空，且包含"有效""无效""有条件通过"三者之一 |
| 交叉评审备注 | 如有交叉评审，需注明（非强制） | 可选检查，不设硬性要求 |

### 4.2 第二部分：上周待办情况
| 审核项 | 硬性要求 | 检查方式 |
|--------|----------|----------|
| 待办列表完整性 | 必须列出所有未完成/本期到期的Action，不得遗漏 | 检查是否存在"待办情况"或"Action"章节，且列表非空 |
| 每个待办的基本要素 | 每个Action必须包含：内容、责任人、计划完成时间、当前状态、完成依据/进展 | 逐一检查各字段是否存在且非空 |
| 计划完成时间格式 | 计划完成时间应为具体日期（如2026-03-05）或"周四18:30" | 检查时间字段是否符合常见日期格式 |
| 逾期合规性 | 若当前时间>计划完成时间，状态必须为"已完成"或"已延期（附批准）" | 比较计划时间与当前时间，逾期且状态为"进行中"或空则不合规 |
| 完成依据 | 若状态为"已完成"，必须提供完成依据（如链接、截图、说明） | 检查完成依据字段是否非空 |
| 延期合规 | 若状态为"已延期"，必须说明延期原因及新计划时间 | 检查延期说明字段是否包含原因和新时间 |

### 4.3 第三部分：正文
#### 4.3.1 基础格式要求
| 审核项 | 硬性要求 | 检查方式 |
|--------|----------|----------|
| 字数限制 | 正文字数≤1000字 | 统计正文文本（不含附录链接），超过则不合规 |
| 图片数量 | 图片≤5张 | 统计正文中图片数量，超过则不合规 |
| 数据来源 | 所有数据必须标注来源 | 检查是否包含"数据来源：""来源："等关键词或引用链接 |
| 图表坐标轴 | 坐标轴必须从0开始 | 建议人工复核，标注"请确认图表坐标轴从0开始" |
| 图表规范 | 二维图表右上为最佳，左下为最差 | 建议人工复核，标注"请确认图表符合右上最佳原则" |
| 颜色规范 | 红色代表好消息，绿色代表坏消息，蓝色代表重点 | 建议人工复核，标注"请确认颜色使用符合规范" |
| 数字格式 | 数字应使用千分位表示（如1,000,000） | 检查连续数字是否遗漏千分位分隔符 |

#### 4.3.2 内容要素要求
| 审核项 | 硬性要求 | 检查方式 |
|--------|----------|----------|
| 结论先行 | 正文应采用"结论—依据—总结"结构 | 检查开头是否包含"结论：""核心观点："，结尾是否有"总结""建议" |
| 议题背景 | 必须说明议题背景（如用户反馈、竞品动态、CEO批注等） | 检查是否包含"背景：""上下文：""问题来源："等关键词 |
| 请示类议题 | 若为请示，必须提供至少两个方案及建议方案 | 检查是否包含"方案一""方案二""建议方案"等关键词 |
| 行动计划 | 如有下一步计划，需明确责任人、时间、交付物 | 检查是否包含"责任人：""时间：""交付物："等结构 |
| 风险分析 | 如有必要，需识别风险并提出应对措施 | 检查是否包含"风险：""应对措施："等关键词 |

### 4.4 第四部分：附录
| 审核项 | 硬性要求 | 检查方式 |
|--------|----------|----------|
| 链接有效性 | 附录内容需通过CF链接或附件提供 | 检查是否存在以"http"开头的链接或附件标记 |
| 链接权限 | 链接需确保相关人员有查看权限 | 人工确认，标注提示 |
| 敏感信息处理 | 若含敏感信息，需设置密码 | 检查是否提及"密码："或附件加密说明 |

## 5. 议题内容质量要求
除上述硬性要求外，议题内容还应满足以下质量要求：
- **议题定义与背景**：议题定义清晰明了，背景说明充分（包含用户/客户反馈、市场/竞品动态、历史问题复盘、CEO批注意见等）。
- **问题识别与分析**：精准识别核心问题，深入分析主客观原因，数据依据充分且交叉验证。
- **方案与计划**：请示类议题至少提供两个可选方案，建议方案理由充分；行动计划具体（责任人、交付物、截止时间），符合SMART原则；涉及资源投入需提供ROI测算或价值预估。
- **风险评估**：识别潜在风险（财务、品牌、技术、合规、人员等），评估可能性及影响，提出切实可行的应对措施。
- **结果导向**：汇报类议题展示关键结果，强调"做好了"而非"做了"；已完成事项附完成依据；遗留Action说明进展及完成标准。
- **价值观体现**：内容符合"成就客户、专业求真、创新卓越、开放合作"的核心价值观，数据真实，不夸大，跨部门协作议题体现沟通共识，创新议题平衡短期与长期价值。

## 6. 审核要点（CEO-1视角）
评审委员（特别是CEO-1及以上）在审阅材料时，可参考以下问题清单进行深度评估：

| 维度 | 审核问题 |
|------|----------|
| **战略对齐** | 1. 议题是否与公司当前战略（如AI化、国际化、价值观筑基）直接相关？ 2. 目标是否量化且可衡量？是否与公司级目标对齐？ |
| **数据与洞察** | 3. 数据来源可靠吗？口径清晰吗？ 4. 分析是否深入洞察了趋势、原因，还是仅罗列事实？ 5. 负面问题是否深入分析了主观原因，并提出改进措施？ |
| **风险与异常** | 6. 是否系统评估了潜在风险？应急预案是否具体？ 7. 异常事项是否第一时间上报？上报时是否附带解决方案？ |
| **方案与执行** | 8. 请示类议题是否提供了多个可选方案？方案对比是否客观？ 9. 行动计划是否具体到人、到时间、到交付物？ 10. 资源估算是否合理？ROI测算是否可信？ |
| **结果与闭环** | 11. 汇报类议题是否清晰展示结果，而非过程？ 12. 遗留Action是否有明确完成标准和跟进计划？ 13. 已完成事项是否复盘并沉淀为组织能力？ |
| **逻辑与表达** | 14. 是否结论先行？核心观点是否被冗余信息淹没？ 15. 表达是否简洁准确、通俗易懂？ |
| **价值观契合** | 16. 方案是否平衡短期利益与长期价值？是否符合"成就客户"？ 17. 是否体现了跨部门协作思考？ |

## 7. 附则
- 本规范自发布之日起执行，与《墨迹天气营销服管理制度》配套使用。
- 解释权归营销服会所有，将根据实际运行情况不定期修订。"""


MEETING_SUBMISSION_REVIEW_OUTPUT_FORMAT = """请按照以下格式输出审核结果：

---

## 上会材料审核报告

### 1. 总体评价
[一句话总结材料整体质量，是否达标]

### 2. 第一部分审核：审核意见
| 审核项 | 结果 | 说明 |
|--------|------|------|
| 作者 | 合规/不合规 | [具体说明] |
| Peer-review人 | 合规/不合规 | [具体说明] |
| Peer-review意见 | 合规/不合规 | [具体说明] |
| 交叉评审备注 | 合规/不适用 | [具体说明] |

### 3. 第二部分审核：上周待办情况
| 审核项 | 结果 | 说明 |
|--------|------|------|
| 待办列表完整性 | 合规/不合规 | [具体说明] |
| 待办基本要素 | 合规/不合规 | [逐个Action检查结果] |
| 时间格式 | 合规/不合规 | [具体说明] |
| 逾期合规性 | 合规/不合规/不适用 | [具体说明] |
| 完成依据 | 合规/不合规/不适用 | [具体说明] |
| 延期合规 | 合规/不合规/不适用 | [具体说明] |

### 4. 第三部分审核：正文
#### 4.1 基础格式
| 审核项 | 结果 | 说明 |
|--------|------|------|
| 字数限制（≤1000字） | 合规/不合规 | [实际字数] |
| 图片数量（≤5张） | 合规/不合规 | [实际数量] |
| 数据来源标注 | 合规/不合规 | [具体说明] |
| 图表坐标轴 | 请人工确认 | [提示说明] |
| 图表规范 | 请人工确认 | [提示说明] |
| 颜色规范 | 请人工确认 | [提示说明] |
| 数字格式 | 合规/不合规 | [具体说明] |

#### 4.2 内容要素
| 审核项 | 结果 | 说明 |
|--------|------|------|
| 结论先行 | 合规/不合规 | [具体说明] |
| 议题背景 | 合规/不合规 | [具体说明] |
| 请示类方案 | 合规/不合规/不适用 | [具体说明] |
| 行动计划 | 合规/不合规/不适用 | [具体说明] |
| 风险分析 | 合规/不合规/不适用 | [具体说明] |

### 5. 第四部分审核：附录
| 审核项 | 结果 | 说明 |
|--------|------|------|
| 链接有效性 | 合规/不合规 | [具体说明] |
| 链接权限 | 请人工确认 | [提示说明] |
| 敏感信息处理 | 合规/不适用 | [具体说明] |

### 6. 内容质量评估
| 维度 | 评价 |
|------|------|
| 议题定义与背景 | [评价] |
| 问题识别与分析 | [评价] |
| 方案与计划 | [评价] |
| 风险评估 | [评价] |
| 结果导向 | [评价] |
| 价值观体现 | [评价] |

### 7. CEO-1视角评估
| 维度 | 评价 |
|------|------|
| 战略对齐 | [评价] |
| 数据与洞察 | [评价] |
| 风险与异常 | [评价] |
| 方案与执行 | [评价] |
| 结果与闭环 | [评价] |
| 逻辑与表达 | [评价] |
| 价值观契合 | [评价] |

### 8. 重点修改建议
[按优先级列出3-5条最重要的修改建议，每条说明原因和改进方向]

### 9. 亮点
[列出材料做得好的1-2个方面]

---"""
