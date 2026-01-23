from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import settings
from app.models.orm import User, RefreshToken, QRCodeSession, LoginLog
from app.services.dingtalk_service import DingTalkService
import secrets
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.dingtalk_service = DingTalkService()

    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    def create_refresh_token(self, user_id: int) -> str:
        """Create and store refresh token"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(refresh_token)
        self.db.commit()
        return token

    def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError:
            return None

    def get_user_by_dingtalk_id(self, dingtalk_user_id: str) -> User:
        """Get user by DingTalk user ID"""
        return self.db.query(User).filter(User.dingtalk_user_id == dingtalk_user_id).first()

    def create_user(self, dingtalk_user_id: str, name: str, email: str = None, avatar_url: str = None) -> User:
        """Create new user"""
        # Check if this is the first user (make them admin)
        user_count = self.db.query(func.count(User.id)).scalar()
        role = "admin" if user_count == 0 else "user"

        user = User(
            dingtalk_user_id=dingtalk_user_id,
            name=name,
            email=email,
            avatar_url=avatar_url,
            role=role,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def log_login(self, user_id: int, login_type: str = "dingtalk", ip_address: str = None, user_agent: str = None):
        """Log user login"""
        log = LoginLog(
            user_id=user_id,
            login_type=login_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)
        self.db.commit()

    async def generate_qrcode_session(self) -> dict:
        """Generate QR code session for DingTalk login"""
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        session = QRCodeSession(
            session_id=session_id,
            status="pending",
            expires_at=expires_at
        )
        self.db.add(session)
        self.db.commit()

        return {
            "session_id": session_id,
            "expires_at": expires_at
        }

    def get_qrcode_session(self, session_id: str) -> QRCodeSession:
        """Get QR code session"""
        return self.db.query(QRCodeSession).filter(QRCodeSession.session_id == session_id).first()

    async def process_qrcode_callback(self, auth_code: str, session_id: str, ip_address: str = None, user_agent: str = None) -> dict:
        """Process DingTalk QR code callback"""
        session = self.get_qrcode_session(session_id)
        if not session or session.status != "pending":
            raise Exception("Invalid or expired session")

        # Get user info from DingTalk using new 3-step API
        user_info = await self.dingtalk_service.get_user_info_by_code(auth_code)
        dingtalk_user_id = user_info.get("userid")

        # Check if user is enterprise employee (has valid userid)
        if not dingtalk_user_id:
            raise Exception("User is not an enterprise employee")

        # Get or create user
        user = self.get_user_by_dingtalk_id(dingtalk_user_id)
        is_new_user = user is None
        if not user:
            user = self.create_user(
                dingtalk_user_id=dingtalk_user_id,
                name=user_info.get("name"),
                email=user_info.get("email"),
                avatar_url=None
            )
        else:
            # Update email if not set and now available
            if not user.email and user_info.get("email"):
                user.email = user_info.get("email")
                self.db.commit()

        # Check if user is active
        if not user.is_active:
            raise Exception("User account is disabled")

        # Update last login time
        user.last_login_at = datetime.utcnow()
        self.db.commit()

        # Log login
        self.log_login(user.id, "dingtalk", ip_address, user_agent)

        # Update session (set 180 days expiry)
        session.status = "completed"
        session.dingtalk_user_id = dingtalk_user_id
        session.expires_at = datetime.utcnow() + timedelta(days=180)
        self.db.commit()

        # Generate tokens
        access_token = self.create_access_token({"sub": str(user.id), "dingtalk_user_id": dingtalk_user_id})
        refresh_token = self.create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user
        }

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token"""
        token_record = self.db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
        if not token_record or token_record.expires_at < datetime.utcnow():
            raise Exception("Invalid or expired refresh token")

        user = token_record.user
        access_token = self.create_access_token({"sub": str(user.id), "dingtalk_user_id": user.dingtalk_user_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
