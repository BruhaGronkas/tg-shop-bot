"""
Authentication system for the web admin panel.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp
from loguru import logger

from config.settings import get_settings
from database.database import SessionLocal
from database.models import User, UserRole

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = settings.jwt_algorithm
SECRET_KEY = settings.jwt_secret_key

# Security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    try:
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def get_user_from_token(token: str) -> Optional[User]:
    """Get user from JWT token."""
    try:
        payload = verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            return user
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting user from token: {e}")
        return None


def get_current_user(request: Request) -> User:
    """Get current authenticated user from request."""
    try:
        # Try to get token from cookie first
        token = request.cookies.get("access_token")
        
        # If no cookie, try Authorization header
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = get_user_from_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(user: User) -> None:
    """Require user to be admin."""
    if user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )


def require_super_admin(user: User) -> None:
    """Require user to be super admin."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin permissions required"
        )


def setup_2fa(user: User) -> dict:
    """Setup 2FA for user."""
    try:
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create TOTP URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email or user.username,
            issuer_name="Telegram Shop Bot"
        )
        
        # Update user (but don't enable 2FA yet)
        db = SessionLocal()
        try:
            user.two_fa_secret = secret
            db.commit()
        finally:
            db.close()
        
        return {
            "secret": secret,
            "qr_uri": provisioning_uri,
            "manual_entry_key": secret
        }
        
    except Exception as e:
        logger.error(f"2FA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup 2FA"
        )


def verify_2fa_token(secret: str, token: str) -> bool:
    """Verify 2FA token."""
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Allow 30 seconds window
    except Exception as e:
        logger.error(f"2FA verification error: {e}")
        return False


def enable_2fa(user: User, token: str) -> bool:
    """Enable 2FA for user after verification."""
    try:
        if not user.two_fa_secret:
            return False
        
        if not verify_2fa_token(user.two_fa_secret, token):
            return False
        
        # Enable 2FA
        db = SessionLocal()
        try:
            user.two_fa_enabled = True
            db.commit()
            return True
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"2FA enable error: {e}")
        return False


def disable_2fa(user: User) -> bool:
    """Disable 2FA for user."""
    try:
        db = SessionLocal()
        try:
            user.two_fa_enabled = False
            user.two_fa_secret = None
            db.commit()
            return True
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"2FA disable error: {e}")
        return False


def create_admin_user(
    username: str,
    email: str,
    password: str,
    role: UserRole = UserRole.ADMIN
) -> User:
    """Create admin user."""
    try:
        db = SessionLocal()
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already exists"
                )
            
            # Create user
            user = User(
                telegram_id=f"admin_{secrets.token_hex(8)}",  # Fake telegram ID
                username=username,
                email=email,
                password_hash=get_password_hash(password),
                role=role,
                is_active=True,
                is_verified=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created admin user: {username}")
            return user
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin user creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin user"
        )


def change_password(user: User, current_password: str, new_password: str) -> bool:
    """Change user password."""
    try:
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            return False
        
        # Update password
        db = SessionLocal()
        try:
            user.password_hash = get_password_hash(new_password)
            user.updated_at = datetime.now(timezone.utc)
            db.commit()
            return True
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return False


def reset_password(user: User, new_password: str) -> bool:
    """Reset user password (admin action)."""
    try:
        db = SessionLocal()
        try:
            user.password_hash = get_password_hash(new_password)
            user.updated_at = datetime.now(timezone.utc)
            # Disable 2FA on password reset for security
            user.two_fa_enabled = False
            user.two_fa_secret = None
            db.commit()
            return True
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        return False


def check_rate_limit(user: User, max_attempts: int = 5, window_minutes: int = 15) -> bool:
    """Check if user has exceeded login rate limit."""
    try:
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return False
        
        if user.login_attempts >= max_attempts:
            # Lock user for window_minutes
            db = SessionLocal()
            try:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=window_minutes)
                db.commit()
            finally:
                db.close()
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        return True  # Allow on error


def increment_login_attempts(user: User) -> None:
    """Increment failed login attempts."""
    try:
        db = SessionLocal()
        try:
            user.login_attempts += 1
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Login attempt increment error: {e}")


def reset_login_attempts(user: User) -> None:
    """Reset failed login attempts."""
    try:
        db = SessionLocal()
        try:
            user.login_attempts = 0
            user.locked_until = None
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Login attempt reset error: {e}")


def generate_api_key(user: User) -> str:
    """Generate API key for user."""
    try:
        # Create long-lived token for API access
        api_token = create_access_token(
            data={"sub": str(user.id), "type": "api"},
            expires_delta=timedelta(days=365)  # 1 year expiry
        )
        
        return api_token
        
    except Exception as e:
        logger.error(f"API key generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API key"
        )


def verify_api_key(api_key: str) -> Optional[User]:
    """Verify API key and return user."""
    try:
        payload = verify_token(api_key)
        if not payload:
            return None
        
        # Check if it's an API token
        if payload.get("type") != "api":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.id == int(user_id),
                User.is_active == True
            ).first()
            return user
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"API key verification error: {e}")
        return None


def get_current_user_optional(request: Request) -> Optional[User]:
    """Get current user without raising exception if not authenticated."""
    try:
        return get_current_user(request)
    except HTTPException:
        return None


class RoleChecker:
    """Role-based access control dependency."""
    
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user


# Role dependencies
require_admin_role = RoleChecker([UserRole.ADMIN, UserRole.MODERATOR])
require_super_admin_role = RoleChecker([UserRole.ADMIN])


def log_admin_action(user: User, action: str, details: dict = None) -> None:
    """Log admin action for audit trail."""
    try:
        from database.models import ActivityLog
        
        db = SessionLocal()
        try:
            activity = ActivityLog(
                user_id=user.id,
                action=f"admin_{action}",
                entity_type="admin",
                entity_id=str(user.id),
                details=details or {},
                created_at=datetime.now(timezone.utc)
            )
            db.add(activity)
            db.commit()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Admin action logging error: {e}")


def create_default_admin():
    """Create default admin user if none exists."""
    try:
        db = SessionLocal()
        try:
            # Check if any admin exists
            admin_exists = db.query(User).filter(
                User.role == UserRole.ADMIN
            ).first()
            
            if not admin_exists:
                # Create default admin
                default_admin = User(
                    telegram_id=f"admin_{secrets.token_hex(8)}",
                    username=settings.admin_username,
                    email=settings.admin_email,
                    password_hash=get_password_hash(settings.admin_password),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True
                )
                
                db.add(default_admin)
                db.commit()
                
                logger.info("Created default admin user")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Default admin creation error: {e}")


# Initialize default admin on import
create_default_admin()