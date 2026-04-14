from fastapi import APIRouter, Depends, HTTPException, WebSocket, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.dependencies.database import get_db
from app.middleware.jwt_auth import get_current_user
from app.services.chat_service import ChatService
from app.services.file_service import file_service
from app.models.schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse
)
from app.models.orm import User, UserFile, Conversation, Message
from app.services.tool_executor import DEFAULT_REVIEW_INSTRUCTIONS
from app.websocket.chat_handler import chat_handler
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel

VALID_REVIEW_TOOLS = set(DEFAULT_REVIEW_INSTRUCTIONS.keys())

class ReviewInstructionUpdate(BaseModel):
    instruction: str

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket endpoint for chat"""
    user = await chat_handler.authenticate_websocket(websocket, db)
    if user:
        await chat_handler.connect(websocket, user.id)
        await chat_handler.handle_message(websocket, user, db)

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation"""
    chat_service = ChatService(db)
    result = chat_service.create_conversation(current_user.id, conversation.title)
    return result

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's conversations"""
    chat_service = ChatService(db)
    return chat_service.get_user_conversations(current_user.id)

@router.get("/conversations/search", response_model=List[ConversationResponse])
async def search_conversations(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search conversations by title"""
    return db.query(Conversation).filter(
        Conversation.user_id == current_user.id,
        Conversation.title.ilike(f"%{q}%")
    ).order_by(
        Conversation.updated_at.desc(),
        Conversation.id.desc()  # Secondary sort key for deterministic ordering
    ).limit(20).all()

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation"""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Delete associated messages first
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.delete(conv)
    db.commit()
    return {"success": True}

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation messages"""
    chat_service = ChatService(db)
    conversation = chat_service.get_conversation(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return chat_service.get_conversation_messages(conversation_id)


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload files (images, documents)"""
    results = await file_service.upload_files(files, current_user.id)

    # Save file records to database
    for result in results:
        user_file = UserFile(
            user_id=current_user.id,
            filename=result["filename"],
            file_path=result["file_path"],
            file_type=result["file_type"],
            file_size=result["file_size"]
        )
        db.add(user_file)

    db.commit()

    return {"urls": [r["url"] for r in results], "files": results}


@router.get("/review-instructions")
async def get_review_instructions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all review instructions (default + custom) for current user"""
    custom = current_user.review_custom_instructions or {}
    result = {}
    for tool_name, default_instruction in DEFAULT_REVIEW_INSTRUCTIONS.items():
        is_custom = tool_name in custom
        result[tool_name] = {
            "instruction": custom[tool_name] if is_custom else default_instruction,
            "is_custom": is_custom,
        }
    return result


@router.put("/review-instructions/{tool_name}")
async def update_review_instruction(
    tool_name: str,
    body: ReviewInstructionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save custom review instruction for a tool"""
    if tool_name not in VALID_REVIEW_TOOLS:
        raise HTTPException(status_code=400, detail=f"Invalid tool_name: {tool_name}")

    custom = dict(current_user.review_custom_instructions or {})
    custom[tool_name] = body.instruction.strip()
    current_user.review_custom_instructions = custom
    db.commit()
    return {"success": True, "tool_name": tool_name, "instruction": custom[tool_name], "is_custom": True}


@router.delete("/review-instructions/{tool_name}")
async def reset_review_instruction(
    tool_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset a custom review instruction to default"""
    if tool_name not in VALID_REVIEW_TOOLS:
        raise HTTPException(status_code=400, detail=f"Invalid tool_name: {tool_name}")

    custom = dict(current_user.review_custom_instructions or {})
    custom.pop(tool_name, None)
    current_user.review_custom_instructions = custom
    db.commit()
    return {"success": True, "tool_name": tool_name, "instruction": DEFAULT_REVIEW_INSTRUCTIONS[tool_name], "is_custom": False}
