from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.dependencies.database import get_db
from app.middleware.jwt_auth import get_current_user
from app.models.orm import User, TokenUsage, LoginLog, SystemLog, Conversation, Message, AccessLog
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class UserResponse(BaseModel):
    id: int
    dingtalk_user_id: str
    name: str
    email: Optional[str]
    avatar_url: Optional[str]
    role: str
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    total_tokens: Optional[int] = 0  # 总 token 消耗
    recent_tokens: Optional[int] = 0  # 最近7天 token 消耗

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class StatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_conversations: int
    total_messages: int
    total_tokens: int
    users_today: int
    messages_today: int


@router.get("/stats", response_model=StatsResponse)
async def get_system_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system statistics"""
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    total_conversations = db.query(func.count(Conversation.id)).scalar()
    total_messages = db.query(func.count(Message.id)).scalar()
    total_tokens = db.query(func.coalesce(func.sum(TokenUsage.total_tokens), 0)).scalar()

    users_today = db.query(func.count(User.id)).filter(
        User.created_at >= today_start
    ).scalar()

    messages_today = db.query(func.count(Message.id)).filter(
        Message.created_at >= today_start
    ).scalar()

    return StatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_tokens=total_tokens,
        users_today=users_today,
        messages_today=messages_today
    )


@router.get("/users")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all users with pagination and token usage stats"""
    query = db.query(User)

    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )

    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()

    # 获取每个用户的 token 消耗统计
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    user_ids = [u.id for u in users]

    # 总消耗
    total_usage = db.query(
        TokenUsage.user_id,
        func.sum(TokenUsage.total_tokens).label("total")
    ).filter(TokenUsage.user_id.in_(user_ids)).group_by(TokenUsage.user_id).all()
    total_map = {r.user_id: r.total or 0 for r in total_usage}

    # 最近7天消耗
    recent_usage = db.query(
        TokenUsage.user_id,
        func.sum(TokenUsage.total_tokens).label("total")
    ).filter(
        TokenUsage.user_id.in_(user_ids),
        TokenUsage.created_at >= seven_days_ago
    ).group_by(TokenUsage.user_id).all()
    recent_map = {r.user_id: r.total or 0 for r in recent_usage}

    # 最近30天消耗（与 Token tab Top10 口径一致）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    monthly_usage = db.query(
        TokenUsage.user_id,
        func.sum(TokenUsage.total_tokens).label("total")
    ).filter(
        TokenUsage.user_id.in_(user_ids),
        TokenUsage.created_at >= thirty_days_ago
    ).group_by(TokenUsage.user_id).all()
    monthly_map = {r.user_id: r.total or 0 for r in monthly_usage}

    return [
        {
            "id": u.id,
            "dingtalk_user_id": u.dingtalk_user_id,
            "name": u.name,
            "email": u.email,
            "avatar_url": u.avatar_url,
            "role": u.role,
            "is_active": u.is_active,
            "last_login_at": u.last_login_at,
            "created_at": u.created_at,
            "total_tokens": total_map.get(u.id, 0),
            "recent_tokens": recent_map.get(u.id, 0),
            "monthly_tokens": monthly_map.get(u.id, 0)
        }
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get user details"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    update: UserUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user (role, active status)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from demoting themselves
    if user.id == admin.id and update.role and update.role != "admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")

    if update.role is not None:
        user.role = update.role
    if update.is_active is not None:
        user.is_active = update.is_active

    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/toggle")
async def toggle_user_status(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle user active status"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot disable yourself")

    user.is_active = not user.is_active
    db.commit()

    return {"success": True, "is_active": user.is_active}


@router.get("/token-usage")
async def get_token_usage(
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[int] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get token usage statistics"""
    start_date = datetime.utcnow() - timedelta(days=days)

    shanghai_date = func.date(func.timezone('Asia/Shanghai', TokenUsage.created_at))

    query = db.query(
        shanghai_date.label("date"),
        func.sum(TokenUsage.prompt_tokens).label("prompt_tokens"),
        func.sum(TokenUsage.completion_tokens).label("completion_tokens"),
        func.sum(TokenUsage.total_tokens).label("total_tokens"),
        func.count(TokenUsage.id).label("request_count")
    ).filter(TokenUsage.created_at >= start_date)

    if user_id:
        query = query.filter(TokenUsage.user_id == user_id)

    daily_usage = query.group_by(shanghai_date).order_by("date").all()

    # Get top users by token usage
    top_users = db.query(
        User.id,
        User.name,
        func.sum(TokenUsage.total_tokens).label("total_tokens")
    ).join(TokenUsage).filter(
        TokenUsage.created_at >= start_date
    ).group_by(User.id, User.name).order_by(
        desc("total_tokens")
    ).limit(10).all()

    return {
        "daily_usage": [
            {
                "date": str(row.date),
                "prompt_tokens": row.prompt_tokens or 0,
                "completion_tokens": row.completion_tokens or 0,
                "total_tokens": row.total_tokens or 0,
                "request_count": row.request_count
            }
            for row in daily_usage
        ],
        "top_users": [
            {"id": row.id, "name": row.name, "total_tokens": row.total_tokens or 0}
            for row in top_users
        ]
    }


@router.get("/login-logs")
async def get_login_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get login logs"""
    query = db.query(LoginLog).outerjoin(User, LoginLog.user_id == User.id)

    if user_id:
        query = query.filter(LoginLog.user_id == user_id)

    logs = query.order_by(desc(LoginLog.created_at)).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_name": log.user.name if log.user else None,
            "login_type": log.login_type,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]


@router.get("/access-logs")
async def get_access_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get access logs (WebSocket session records)"""
    query = db.query(AccessLog).outerjoin(User, AccessLog.user_id == User.id)
    if user_id:
        query = query.filter(AccessLog.user_id == user_id)
    logs = query.order_by(desc(AccessLog.created_at)).offset(skip).limit(limit).all()
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_name": log.user.name if log.user else None,
            "access_type": log.access_type,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/logs")
async def get_system_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    level: Optional[str] = None,
    module: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system logs"""
    query = db.query(SystemLog)

    if level:
        query = query.filter(SystemLog.level == level)
    if module:
        query = query.filter(SystemLog.module == module)

    logs = query.order_by(desc(SystemLog.created_at)).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "level": log.level,
            "module": log.module,
            "message": log.message,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]


# Helper function to log system events
def log_system_event(db: Session, level: str, module: str, message: str, details: dict = None):
    """Log a system event"""
    log = SystemLog(
        level=level,
        module=module,
        message=message,
        details=details
    )
    db.add(log)
    db.commit()
