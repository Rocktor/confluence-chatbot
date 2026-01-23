from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Auth schemas
class QRCodeResponse(BaseModel):
    session_id: str
    qrcode_url: str
    expires_at: datetime

class QRCodeStatusResponse(BaseModel):
    status: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[dict] = None

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# User schemas
class UserResponse(BaseModel):
    id: int
    dingtalk_user_id: str
    name: str
    email: Optional[str]
    avatar_url: Optional[str]
    role: Optional[str] = "user"
    created_at: datetime

    class Config:
        from_attributes = True

# Conversation schemas
class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Message schemas
class MessageCreate(BaseModel):
    conversation_id: int
    content: str
    image_url: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    image_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Confluence schemas
class ConfluenceConfigCreate(BaseModel):
    base_url: str
    email: str  # 用户名格式，不是邮箱
    api_token: str
    space_key: Optional[str] = None

class ConfluenceConfigResponse(BaseModel):
    id: int
    base_url: str
    email: str
    space_key: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ConfluencePageCreate(BaseModel):
    space_key: str
    title: str
    content: str
    parent_id: Optional[str] = None

class ConfluencePageUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class ConfluencePageResponse(BaseModel):
    id: int
    page_id: str
    title: str
    space_key: Optional[str]
    last_synced_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class ConfluenceSyncRequest(BaseModel):
    page_url: str

class ChatMessage(BaseModel):
    role: str
    content: str
    image_url: Optional[str] = None
