"""
FastAPI web application for the admin panel.
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends, status, Form, File, UploadFile, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import pyotp
from loguru import logger

from config.settings import get_settings
from database.database import get_db, SessionLocal, init_db
from database.models import (
    User, Product, Category, Order, Payment, DiscountCode,
    SupportTicket, Analytics, BackupLog, UserRole, OrderStatus, PaymentStatus
)
from services.nowpayments import nowpayments_service
from services.qr_generator import qr_generator
from .auth import (
    verify_password, create_access_token, verify_token,
    get_current_user, require_admin, setup_2fa, verify_2fa_token
)
from .api import router as api_router
from .utils import (
    generate_sales_report, create_backup, send_notification,
    get_analytics_data, export_to_csv, export_to_xlsx, export_to_pdf
)

settings = get_settings()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Templates
templates = Jinja2Templates(directory="web/templates")

# Security
security = HTTPBearer()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Telegram Shop Bot Admin Panel",
        description="Comprehensive admin panel for managing the Telegram shop bot",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None
    )
    
    # Add middleware
    app.add_middleware(SlowAPIMiddleware)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
        )
    
    # Mount static files
    static_path = Path("web/static")
    static_path.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory="web/static"), name="static")
    
    # Initialize database
    init_db()
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Admin Panel Routes
    
    @app.get("/", response_class=HTMLResponse)
    @limiter.limit("10/minute")
    async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
        """Main dashboard."""
        try:
            require_admin(current_user)
            
            db = SessionLocal()
            try:
                # Get dashboard statistics
                total_users = db.query(User).count()
                total_orders = db.query(Order).count()
                total_revenue = db.query(Order).filter(
                    Order.status == OrderStatus.PAID
                ).with_entities(
                    db.func.sum(Order.total_amount)
                ).scalar() or 0
                
                pending_orders = db.query(Order).filter(
                    Order.status == OrderStatus.PENDING
                ).count()
                
                recent_orders = db.query(Order).order_by(
                    Order.created_at.desc()
                ).limit(10).all()
                
                # Get analytics data
                analytics_data = await get_analytics_data(db, days=30)
                
                return templates.TemplateResponse(
                    "dashboard.html",
                    {
                        "request": request,
                        "user": current_user,
                        "total_users": total_users,
                        "total_orders": total_orders,
                        "total_revenue": total_revenue,
                        "pending_orders": pending_orders,
                        "recent_orders": recent_orders,
                        "analytics_data": analytics_data
                    }
                )
                
            finally:
                db.close()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/login", response_class=HTMLResponse)
    @limiter.limit("10/minute")
    async def login_page(request: Request):
        """Login page."""
        return templates.TemplateResponse("login.html", {"request": request})
    
    @app.post("/login")
    @limiter.limit("5/minute")
    async def login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        totp_code: Optional[str] = Form(None)
    ):
        """Handle login."""
        try:
            db = SessionLocal()
            try:
                user = db.query(User).filter(
                    User.username == username,
                    User.role.in_([UserRole.ADMIN, UserRole.MODERATOR])
                ).first()
                
                if not user or not verify_password(password, user.password_hash):
                    return templates.TemplateResponse(
                        "login.html",
                        {"request": request, "error": "Invalid credentials"}
                    )
                
                # Check 2FA if enabled
                if user.two_fa_enabled:
                    if not totp_code:
                        return templates.TemplateResponse(
                            "login.html",
                            {"request": request, "show_2fa": True, "username": username}
                        )
                    
                    if not verify_2fa_token(user.two_fa_secret, totp_code):
                        return templates.TemplateResponse(
                            "login.html",
                            {"request": request, "error": "Invalid 2FA code", "show_2fa": True}
                        )
                
                # Update last login
                user.last_login = datetime.utcnow()
                user.login_attempts = 0
                db.commit()
                
                # Create access token
                token = create_access_token(data={"sub": str(user.id)})
                
                response = RedirectResponse(url="/", status_code=302)
                response.set_cookie("access_token", token, httponly=True, secure=not settings.debug)
                return response
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Login failed"}
            )
    
    @app.get("/logout")
    async def logout():
        """Handle logout."""
        response = RedirectResponse(url="/login", status_code=302)
        response.delete_cookie("access_token")
        return response
    
    @app.get("/products", response_class=HTMLResponse)
    @limiter.limit("30/minute")
    async def products_page(
        request: Request,
        page: int = 1,
        search: Optional[str] = None,
        category: Optional[int] = None,
        current_user: User = Depends(get_current_user)
    ):
        """Products management page."""
        try:
            require_admin(current_user)
            
            db = SessionLocal()
            try:
                # Build query
                query = db.query(Product)
                
                if search:
                    query = query.filter(Product.name.contains(search))
                
                if category:
                    query = query.filter(Product.category_id == category)
                
                # Pagination
                per_page = 20
                offset = (page - 1) * per_page
                products = query.offset(offset).limit(per_page).all()
                total_products = query.count()
                total_pages = (total_products + per_page - 1) // per_page
                
                # Get categories for filter
                categories = db.query(Category).all()
                
                return templates.TemplateResponse(
                    "products.html",
                    {
                        "request": request,
                        "user": current_user,
                        "products": products,
                        "categories": categories,
                        "current_page": page,
                        "total_pages": total_pages,
                        "search": search,
                        "selected_category": category
                    }
                )
                
            finally:
                db.close()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Products page error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/orders", response_class=HTMLResponse)
    @limiter.limit("30/minute")
    async def orders_page(
        request: Request,
        page: int = 1,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        current_user: User = Depends(get_current_user)
    ):
        """Orders management page."""
        try:
            require_admin(current_user)
            
            db = SessionLocal()
            try:
                # Build query
                query = db.query(Order).join(User)
                
                if status_filter:
                    query = query.filter(Order.status == status_filter)
                
                if search:
                    query = query.filter(
                        db.or_(
                            Order.order_number.contains(search),
                            User.username.contains(search),
                            User.first_name.contains(search)
                        )
                    )
                
                # Order by newest first
                query = query.order_by(Order.created_at.desc())
                
                # Pagination
                per_page = 20
                offset = (page - 1) * per_page
                orders = query.offset(offset).limit(per_page).all()
                total_orders = query.count()
                total_pages = (total_orders + per_page - 1) // per_page
                
                return templates.TemplateResponse(
                    "orders.html",
                    {
                        "request": request,
                        "user": current_user,
                        "orders": orders,
                        "current_page": page,
                        "total_pages": total_pages,
                        "status_filter": status_filter,
                        "search": search,
                        "order_statuses": [status.value for status in OrderStatus]
                    }
                )
                
            finally:
                db.close()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Orders page error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/users", response_class=HTMLResponse)
    @limiter.limit("30/minute")
    async def users_page(
        request: Request,
        page: int = 1,
        search: Optional[str] = None,
        role_filter: Optional[str] = None,
        current_user: User = Depends(get_current_user)
    ):
        """Users management page."""
        try:
            require_admin(current_user)
            
            db = SessionLocal()
            try:
                # Build query
                query = db.query(User)
                
                if search:
                    query = query.filter(
                        db.or_(
                            User.username.contains(search),
                            User.first_name.contains(search),
                            User.email.contains(search)
                        )
                    )
                
                if role_filter:
                    query = query.filter(User.role == role_filter)
                
                # Order by newest first
                query = query.order_by(User.created_at.desc())
                
                # Pagination
                per_page = 20
                offset = (page - 1) * per_page
                users = query.offset(offset).limit(per_page).all()
                total_users = query.count()
                total_pages = (total_users + per_page - 1) // per_page
                
                return templates.TemplateResponse(
                    "users.html",
                    {
                        "request": request,
                        "user": current_user,
                        "users": users,
                        "current_page": page,
                        "total_pages": total_pages,
                        "search": search,
                        "role_filter": role_filter,
                        "user_roles": [role.value for role in UserRole]
                    }
                )
                
            finally:
                db.close()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Users page error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/analytics", response_class=HTMLResponse)
    @limiter.limit("20/minute")
    async def analytics_page(
        request: Request,
        period: str = "30d",
        current_user: User = Depends(get_current_user)
    ):
        """Analytics and reports page."""
        try:
            require_admin(current_user)
            
            db = SessionLocal()
            try:
                # Parse period
                days = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}.get(period, 30)
                
                # Get analytics data
                analytics_data = await get_analytics_data(db, days=days)
                
                return templates.TemplateResponse(
                    "analytics.html",
                    {
                        "request": request,
                        "user": current_user,
                        "analytics_data": analytics_data,
                        "period": period
                    }
                )
                
            finally:
                db.close()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Analytics page error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/support", response_class=HTMLResponse)
    @limiter.limit("30/minute")
    async def support_page(
        request: Request,
        page: int = 1,
        status_filter: Optional[str] = None,
        current_user: User = Depends(get_current_user)
    ):
        """Support tickets page."""
        try:
            require_admin(current_user)
            
            db = SessionLocal()
            try:
                # Build query
                query = db.query(SupportTicket).join(User)
                
                if status_filter:
                    query = query.filter(SupportTicket.status == status_filter)
                
                # Order by priority and creation date
                query = query.order_by(
                    SupportTicket.priority.desc(),
                    SupportTicket.created_at.desc()
                )
                
                # Pagination
                per_page = 20
                offset = (page - 1) * per_page
                tickets = query.offset(offset).limit(per_page).all()
                total_tickets = query.count()
                total_pages = (total_tickets + per_page - 1) // per_page
                
                return templates.TemplateResponse(
                    "support.html",
                    {
                        "request": request,
                        "user": current_user,
                        "tickets": tickets,
                        "current_page": page,
                        "total_pages": total_pages,
                        "status_filter": status_filter
                    }
                )
                
            finally:
                db.close()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Support page error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/settings", response_class=HTMLResponse)
    @limiter.limit("10/minute")
    async def settings_page(
        request: Request,
        current_user: User = Depends(get_current_user)
    ):
        """Settings page."""
        try:
            require_admin(current_user)
            
            return templates.TemplateResponse(
                "settings.html",
                {
                    "request": request,
                    "user": current_user,
                    "settings": settings
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Settings page error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # File download endpoints
    @app.get("/download/reports/{filename}")
    async def download_report(
        filename: str,
        current_user: User = Depends(get_current_user)
    ):
        """Download generated reports."""
        try:
            require_admin(current_user)
            
            file_path = Path(f"exports/{filename}")
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/octet-stream"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise HTTPException(status_code=500, detail="Download failed")
    
    # Webhook endpoints
    @app.post("/webhook/telegram")
    @limiter.limit("100/minute")
    async def telegram_webhook(request: Request):
        """Telegram bot webhook endpoint."""
        try:
            data = await request.json()
            
            # Process webhook data with bot
            from bot.bot import telegram_bot
            
            if telegram_bot.application:
                # Convert to Update object and process
                from telegram import Update
                update = Update.de_json(data, telegram_bot.application.bot)
                await telegram_bot.application.process_update(update)
            
            return {"status": "ok"}
            
        except Exception as e:
            logger.error(f"Telegram webhook error: {e}")
            return {"status": "error", "message": str(e)}
    
    @app.post("/webhook/payment-ipn")
    @limiter.limit("100/minute")
    async def payment_ipn(request: Request):
        """NOWPayments IPN webhook endpoint."""
        try:
            # Verify signature
            signature = request.headers.get("x-nowpayments-sig")
            body = await request.body()
            
            if not signature or not await nowpayments_service.verify_ipn_signature(
                body.decode(), signature
            ):
                raise HTTPException(status_code=400, detail="Invalid signature")
            
            # Process IPN
            data = json.loads(body)
            success = await nowpayments_service.process_ipn_callback(data)
            
            if success:
                return {"status": "ok"}
            else:
                return {"status": "error"}, 400
                
        except Exception as e:
            logger.error(f"Payment IPN error: {e}")
            return {"status": "error", "message": str(e)}, 500
    
    # Background task endpoints
    @app.post("/admin/backup")
    async def create_backup_endpoint(
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_user)
    ):
        """Create database backup."""
        try:
            require_admin(current_user)
            
            background_tasks.add_task(create_backup)
            return {"status": "Backup started"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Backup error: {e}")
            raise HTTPException(status_code=500, detail="Backup failed")
    
    return app


# Create the app instance
app = create_app()