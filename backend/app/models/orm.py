from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    dingtalk_user_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    avatar_url = Column(Text)
    role = Column(String(50), default="user")  # user, admin
    is_active = Column(Boolean, default=True)
    last_login_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    conversations = relationship("Conversation", back_populates="user")
    confluence_configs = relationship("ConfluenceConfig", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    files = relationship("UserFile", back_populates="user")
    token_usages = relationship("TokenUsage", back_populates="user")
    login_logs = relationship("LoginLog", back_populates="user")
    access_logs = relationship("AccessLog", back_populates="user")

class QRCodeSession(Base):
    __tablename__ = "qrcode_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    qrcode_url = Column(Text, nullable=True)
    status = Column(String(50), default="pending", index=True)
    dingtalk_user_id = Column(String(255))
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title = Column(String(500))
    confluence_page_id = Column(Integer, ForeignKey("confluence_pages.id", ondelete="SET NULL"), nullable=True)
    context_type = Column(String(50), default="general")  # general, confluence
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    confluence_page = relationship("ConfluencePage", back_populates="conversations")
    token_usages = relationship("TokenUsage", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(Text)
    file_urls = Column(JSONB, default=[])  # 附件URL列表
    created_at = Column(TIMESTAMP, server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")

class ConfluenceConfig(Base):
    __tablename__ = "confluence_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    base_url = Column(String(500), nullable=False)
    email = Column(String(255), nullable=False)
    api_token_encrypted = Column(Text, nullable=False)
    space_key = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="confluence_configs")
    pages = relationship("ConfluencePage", back_populates="config")

class ConfluencePage(Base):
    __tablename__ = "confluence_pages"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("confluence_configs.id", ondelete="CASCADE"), index=True)
    page_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    space_key = Column(String(255))
    content_markdown = Column(Text)
    last_synced_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    config = relationship("ConfluenceConfig", back_populates="pages")
    chunks = relationship("DocumentChunk", back_populates="page")
    conversations = relationship("Conversation", back_populates="confluence_page")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("confluence_pages.id", ondelete="CASCADE"), index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))
    chunk_metadata = Column("metadata", JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now())

    page = relationship("ConfluencePage", back_populates="chunks")


class UserFile(Base):
    __tablename__ = "user_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="files")


class TokenUsage(Base):
    __tablename__ = "token_usages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    model = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="token_usages")
    conversation = relationship("Conversation", back_populates="token_usages")


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    login_type = Column(String(50), default="dingtalk")
    ip_address = Column(String(50))
    user_agent = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="login_logs")


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    access_type = Column(String(50), default="ws_session")
    ip_address = Column(String(50))
    user_agent = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="access_logs")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), index=True)  # info, warning, error
    module = Column(String(100))
    message = Column(Text)
    details = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
