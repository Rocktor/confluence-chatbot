from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.dependencies.database import get_db, SessionLocal
from app.services.chat_service import ChatService
from jose import jwt, JWTError
from app.config import settings
from app.models.orm import User, AccessLog
import json

TOOL_DISPLAY_NAMES = {
    "read_confluence_page": "读取页面",
    "edit_confluence_page": "精确编辑",
    "insert_content_to_confluence_page": "插入内容",
    "update_confluence_page": "更新页面",
    "create_confluence_page": "创建页面",
    "search_confluence": "搜索页面",
    "view_confluence_image": "查看图片"
}

class ChatWebSocketHandler:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect WebSocket"""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        """Disconnect WebSocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def authenticate_websocket(self, websocket: WebSocket, db: Session) -> User:
        """Authenticate WebSocket connection"""
        # Get token from query params or headers
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return None

        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=1008, reason="Invalid token")
                return None

            user = db.query(User).filter(User.id == int(user_id)).first()
            if not user:
                await websocket.close(code=1008, reason="User not found")
                return None

            ip_address = (
                websocket.headers.get("x-forwarded-for", "").split(",")[0].strip()
                or websocket.headers.get("x-real-ip")
                or (websocket.client.host if websocket.client else None)
            )
            user_agent = websocket.headers.get("user-agent")
            log_db = SessionLocal()
            try:
                log = AccessLog(
                    user_id=user.id,
                    access_type="ws_session",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                log_db.add(log)
                log_db.commit()
            finally:
                log_db.close()

            return user
        except JWTError:
            await websocket.close(code=1008, reason="Invalid token")
            return None

    async def handle_message(
        self,
        websocket: WebSocket,
        user: User,
        db: Session
    ):
        """Handle incoming WebSocket messages with AI Agent tool support"""
        chat_service = ChatService(db, user_id=user.id)

        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)

                conversation_id = message_data.get("conversation_id")
                content = message_data.get("content")
                # Support both single image_url and array image_urls
                image_urls = message_data.get("image_urls", [])
                if not image_urls:
                    single_url = message_data.get("image_url")
                    if single_url:
                        image_urls = [single_url]

                # Get file_urls for document parsing
                file_urls = message_data.get("file_urls", [])

                # Parse model selection
                model = message_data.get("model", "gpt-5.1")
                ALLOWED_MODELS = {"gpt-5.1", "gpt-5.2", "gpt-5.4", "gpt-5.4-pro", "gemini-3-pro"}
                if model not in ALLOWED_MODELS:
                    model = "gpt-5.1"

                # Create conversation if not exists
                if not conversation_id:
                    conversation = chat_service.create_conversation(user.id)
                    conversation_id = conversation.id
                    await websocket.send_json({
                        "type": "conversation_created",
                        "conversation_id": conversation_id
                    })
                    # Generate title from first message (async, don't block)
                    try:
                        title = await chat_service.generate_title(content)
                        chat_service.update_conversation_title(conversation_id, title)
                        await websocket.send_json({
                            "type": "title_updated",
                            "conversation_id": conversation_id,
                            "title": title
                        })
                    except Exception:
                        pass  # Title generation is non-critical

                # Stream response with tool support
                await websocket.send_json({"type": "stream_start"})

                async for chunk in chat_service.chat_stream_with_tools(
                    conversation_id, content, user.id, image_urls, file_urls, model=model
                ):
                    if chunk["type"] == "thinking":
                        await websocket.send_json({
                            "type": "thinking",
                            "content": chunk["content"]
                        })
                    elif chunk["type"] == "content":
                        await websocket.send_json({
                            "type": "stream_chunk",
                            "content": chunk["content"]
                        })
                    elif chunk["type"] == "tool_call":
                        display_name = TOOL_DISPLAY_NAMES.get(chunk["tool_name"], chunk["tool_name"])
                        await websocket.send_json({
                            "type": "tool_call",
                            "tool_name": chunk["tool_name"],
                            "display_name": display_name,
                            "status": chunk["status"]
                        })
                    elif chunk["type"] == "tool_result":
                        display_name = TOOL_DISPLAY_NAMES.get(chunk["tool_name"], chunk["tool_name"])
                        await websocket.send_json({
                            "type": "tool_result",
                            "tool_name": chunk["tool_name"],
                            "display_name": display_name,
                            "result": chunk["result"]
                        })
                        # Send new stream_start for AI response after tool execution
                        await websocket.send_json({"type": "stream_start"})
                    elif chunk["type"] == "done":
                        pass

                await websocket.send_json({"type": "stream_end"})

        except WebSocketDisconnect:
            self.disconnect(user.id)
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
            self.disconnect(user.id)

chat_handler = ChatWebSocketHandler()
