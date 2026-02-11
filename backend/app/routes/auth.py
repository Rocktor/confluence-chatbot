from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies.database import get_db
from app.middleware.jwt_auth import get_current_user
from app.services.auth_service import AuthService
from app.config import settings
from app.models.schemas import (
    QRCodeResponse,
    QRCodeStatusResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserResponse
)
from app.models.orm import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/qrcode/generate")
async def generate_qrcode(db: Session = Depends(get_db)):
    """Generate QR code session for DingTalk login"""
    auth_service = AuthService(db)
    result = await auth_service.generate_qrcode_session()
    return {
        "state": result["session_id"],
        "client_id": settings.DINGTALK_APP_KEY,
        "redirect_uri": f"{settings.APP_BASE_URL}/login"
    }

@router.get("/qrcode/status/{session_id}", response_model=QRCodeStatusResponse)
async def get_qrcode_status(session_id: str, db: Session = Depends(get_db)):
    """Get QR code scan status"""
    auth_service = AuthService(db)
    session = auth_service.get_qrcode_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "completed":
        # Generate tokens for completed session
        user = auth_service.get_user_by_dingtalk_id(session.dingtalk_user_id)
        access_token = auth_service.create_access_token({
            "sub": str(user.id),
            "dingtalk_user_id": user.dingtalk_user_id
        })
        refresh_token = auth_service.create_refresh_token(user.id)

        return {
            "status": "completed",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "role": user.role
            }
        }

    return {"status": session.status}

@router.post("/qrcode/callback")
async def qrcode_callback(code: str, state: str, request: Request, db: Session = Depends(get_db)):
    """Handle DingTalk QR code callback"""
    auth_service = AuthService(db)
    try:
        ip_address = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.headers.get("x-real-ip")
            or (request.client.host if request.client else None)
        )
        user_agent = request.headers.get("user-agent")
        result = await auth_service.process_qrcode_callback(code, state, ip_address, user_agent)
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "user": {
                "id": result["user"].id,
                "name": result["user"].name,
                "email": result["user"].email,
                "avatar_url": result["user"].avatar_url,
                "role": result["user"].role
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token"""
    auth_service = AuthService(db)
    try:
        result = auth_service.refresh_access_token(request.refresh_token)
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user
