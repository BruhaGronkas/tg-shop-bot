"""
Database models for the Telegram Shop Bot.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, 
    ForeignKey, JSON, Enum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from database.database import Base


# Enums
class UserRole(PyEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    MODERATOR = "moderator"


class OrderStatus(PyEnum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(PyEnum):
    PENDING = "pending"
    WAITING = "waiting"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    SENDING = "sending"
    PARTIALLY_PAID = "partially_paid"
    FINISHED = "finished"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class ProductType(PyEnum):
    DIGITAL = "digital"
    PHYSICAL = "physical"


class TicketStatus(PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class BackupStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Models
class User(Base):
    """User model for customers and admins."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    language = Column(String, default="en")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Security
    password_hash = Column(String)  # For admin panel access
    two_fa_secret = Column(String)
    two_fa_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # Loyalty & Referral
    loyalty_points = Column(Integer, default=0)
    referral_code = Column(String, unique=True, index=True)
    referred_by_id = Column(Integer, ForeignKey("users.id"))
    total_spent = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    tickets = relationship("SupportTicket", back_populates="user")
    referrals = relationship("User", remote_side=[id])
    referred_by = relationship("User", remote_side=[id], back_populates="referrals")


class Category(Base):
    """Product category model."""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    image_url = Column(String)
    parent_id = Column(Integer, ForeignKey("categories.id"))
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    # SEO
    slug = Column(String, unique=True, index=True)
    meta_title = Column(String)
    meta_description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="category")
    subcategories = relationship("Category", remote_side=[id])
    parent = relationship("Category", remote_side=[id], back_populates="subcategories")


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    short_description = Column(String)
    price = Column(Float, nullable=False)
    compare_price = Column(Float)  # Original price for discounts
    
    # Product details
    sku = Column(String, unique=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    product_type = Column(Enum(ProductType), default=ProductType.DIGITAL)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Inventory
    track_inventory = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)
    allow_backorder = Column(Boolean, default=False)
    
    # Digital product settings
    digital_file_url = Column(String)
    download_limit = Column(Integer)
    download_expiry_days = Column(Integer)
    
    # Physical product settings
    weight = Column(Float)
    length = Column(Float)
    width = Column(Float)
    height = Column(Float)
    requires_shipping = Column(Boolean, default=True)
    
    # Media
    images = Column(JSON)  # List of image URLs
    video_url = Column(String)
    
    # SEO
    slug = Column(String, unique=True, index=True)
    meta_title = Column(String)
    meta_description = Column(Text)
    
    # Analytics
    view_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    
    # Indexes
    __table_args__ = (
        Index('idx_product_category_active', 'category_id', 'is_active'),
        Index('idx_product_price', 'price'),
    )


class Order(Base):
    """Order model."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Order details
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    subtotal = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    shipping_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    
    # Payment
    payment_method = Column(String)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Discounts & Promotions
    discount_code = Column(String)
    loyalty_points_used = Column(Integer, default=0)
    
    # Shipping
    shipping_address = Column(JSON)
    billing_address = Column(JSON)
    shipping_method = Column(String)
    tracking_number = Column(String)
    
    # Notes
    customer_notes = Column(Text)
    admin_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    shipped_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payments = relationship("Payment", back_populates="order")
    
    # Indexes
    __table_args__ = (
        Index('idx_order_user_status', 'user_id', 'status'),
        Index('idx_order_created', 'created_at'),
    )


class OrderItem(Base):
    """Order item model."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    # Item details
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Product snapshot (in case product changes)
    product_name = Column(String, nullable=False)
    product_sku = Column(String)
    product_data = Column(JSON)  # Full product data at time of order
    
    # Digital delivery
    download_links = Column(JSON)
    download_count = Column(Integer, default=0)
    download_expires_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base):
    """Payment model for crypto payments via NOWPayments."""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    
    # NOWPayments fields
    payment_id = Column(String, unique=True, index=True)  # NOWPayments payment ID
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    pay_address = Column(String)  # Crypto address to pay to
    price_amount = Column(Float, nullable=False)
    price_currency = Column(String, nullable=False)
    pay_amount = Column(Float)
    pay_currency = Column(String)
    
    # Payment details
    actually_paid = Column(Float, default=0.0)
    actually_paid_currency = Column(String)
    purchase_id = Column(String)  # Our internal reference
    payment_extra_id = Column(String)
    
    # QR Code
    qr_code_url = Column(String)
    payment_url = Column(String)
    
    # Transaction details
    txn_id = Column(String)  # Blockchain transaction ID
    network = Column(String)
    network_precision = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_status', 'payment_status'),
        Index('idx_payment_created', 'created_at'),
    )


class DiscountCode(Base):
    """Discount code model."""
    __tablename__ = "discount_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Discount settings
    type = Column(String, nullable=False)  # percentage, fixed_amount, free_shipping
    value = Column(Float, nullable=False)
    minimum_amount = Column(Float, default=0.0)
    maximum_amount = Column(Float)
    
    # Usage limits
    usage_limit = Column(Integer)  # Total usage limit
    usage_limit_per_customer = Column(Integer, default=1)
    current_usage = Column(Integer, default=0)
    
    # Validity
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    
    # Targeting
    applies_to_products = Column(JSON)  # List of product IDs
    applies_to_categories = Column(JSON)  # List of category IDs
    customer_eligibility = Column(String, default="all")  # all, new, existing
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class LoyaltyTransaction(Base):
    """Loyalty points transaction model."""
    __tablename__ = "loyalty_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    
    # Transaction details
    points = Column(Integer, nullable=False)  # Positive for earned, negative for spent
    type = Column(String, nullable=False)  # earned, spent, expired, adjustment
    description = Column(String, nullable=False)
    reference = Column(String)  # Reference to related record
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SupportTicket(Base):
    """Customer support ticket model."""
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Ticket details
    subject = Column(String, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(String, default="normal")  # low, normal, high, urgent
    category = Column(String)
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="tickets", foreign_keys=[user_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    messages = relationship("SupportMessage", back_populates="ticket")


class SupportMessage(Base):
    """Support ticket message model."""
    __tablename__ = "support_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Message details
    message = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal notes vs customer messages
    attachments = Column(JSON)  # List of attachment URLs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="messages")
    user = relationship("User")


class Analytics(Base):
    """Analytics data model."""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_type = Column(String, nullable=False, index=True)
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_date_type', 'date', 'metric_type'),
        UniqueConstraint('date', 'metric_type', 'metric_name', name='unique_daily_metric'),
    )


class BackupLog(Base):
    """Backup operation log model."""
    __tablename__ = "backup_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    backup_type = Column(String, nullable=False)  # full, incremental, manual
    status = Column(Enum(BackupStatus), default=BackupStatus.PENDING)
    file_path = Column(String)
    file_size = Column(Integer)
    
    # Details
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    tables_backed_up = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemSetting(Base):
    """System settings model."""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    category = Column(String, default="general")
    is_public = Column(Boolean, default=False)  # Can be accessed via API
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ActivityLog(Base):
    """Activity log for admin actions."""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    entity_type = Column(String)  # product, order, user, etc.
    entity_id = Column(String)
    details = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_activity_user_created', 'user_id', 'created_at'),
        Index('idx_activity_entity', 'entity_type', 'entity_id'),
    )