"""
Utility functions for the Telegram shop bot.
"""
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from telegram import User as TelegramUser
from loguru import logger

from database.database import SessionLocal
from database.models import User, Product, Order, UserRole, ProductType
from config.settings import get_settings

settings = get_settings()

# Simple translation dictionary (in production, use proper i18n)
TRANSLATIONS = {
    "en": {
        "🛍️ Browse Products": "🛍️ Browse Products",
        "🛒 My Cart": "🛒 My Cart",
        "📦 My Orders": "📦 My Orders",
        "👤 Profile": "👤 Profile",
        "🎁 Referrals": "🎁 Referrals",
        "🎯 Promotions": "🎯 Promotions",
        "💡 Support": "💡 Support",
        "🌐 Language": "🌐 Language",
        "ℹ️ Help": "ℹ️ Help",
        "« Back to Menu": "« Back to Menu",
        "« Back to Category": "« Back to Category",
        "➕ Add 1 to Cart": "➕ Add 1 to Cart",
        "🛒 Add 3 to Cart": "🛒 Add 3 to Cart",
        "🛒 Add 5 to Cart": "🛒 Add 5 to Cart",
        "❌ Out of Stock": "❌ Out of Stock",
        "📝 Reviews": "📝 Reviews",
        "📤 Share": "📤 Share",
        "💳 Checkout": "💳 Checkout",
        "🗑️ Clear Cart": "🗑️ Clear Cart",
        "📝 Edit Items": "📝 Edit Items",
        "🛍️ Continue Shopping": "🛍️ Continue Shopping",
        "₿ Bitcoin (BTC)": "₿ Bitcoin (BTC)",
        "Ξ Ethereum (ETH)": "Ξ Ethereum (ETH)",
        "₮ Tether (USDT)": "₮ Tether (USDT)",
        "🔗 Chainlink (LINK)": "🔗 Chainlink (LINK)",
        "🪙 More Cryptos": "🪙 More Cryptos",
        "« Back to Cart": "« Back to Cart",
        "🔄 Refresh Status": "🔄 Refresh Status",
        "❓ Payment Help": "❓ Payment Help",
        "📞 Contact Support": "📞 Contact Support",
        "Check Payment Status": "Check Payment Status",
        "More Cryptocurrencies": "More Cryptocurrencies",
        "Welcome to our crypto shop! 🛍️\n\nYou can browse our products, make purchases with cryptocurrency, and track your orders all from this bot.\n\nUse /menu to see available options or click the button below.": "Welcome to our crypto shop! 🛍️\n\nYou can browse our products, make purchases with cryptocurrency, and track your orders all from this bot.\n\nUse /menu to see available options or click the button below.",
    },
    "lt": {
        "🛍️ Browse Products": "🛍️ Naršyti produktus",
        "🛒 My Cart": "🛒 Mano krepšelis",
        "📦 My Orders": "📦 Mano užsakymai",
        "👤 Profile": "👤 Profilis",
        "🎁 Referrals": "🎁 Referalai",
        "🎯 Promotions": "🎯 Akcijos",
        "💡 Support": "💡 Pagalba",
        "🌐 Language": "🌐 Kalba",
        "ℹ️ Help": "ℹ️ Pagalba",
        "« Back to Menu": "« Grįžti į meniu",
        "« Back to Category": "« Grįžti į kategoriją",
        "➕ Add 1 to Cart": "➕ Pridėti 1 į krepšelį",
        "🛒 Add 3 to Cart": "🛒 Pridėti 3 į krepšelį",
        "🛒 Add 5 to Cart": "🛒 Pridėti 5 į krepšelį",
        "❌ Out of Stock": "❌ Išparduota",
        "📝 Reviews": "📝 Atsiliepimai",
        "📤 Share": "📤 Dalintis",
        "💳 Checkout": "💳 Apmokėti",
        "🗑️ Clear Cart": "🗑️ Išvalyti krepšelį",
        "📝 Edit Items": "📝 Redaguoti prekes",
        "🛍️ Continue Shopping": "🛍️ Tęsti apsipirkimą",
        "₿ Bitcoin (BTC)": "₿ Bitcoin (BTC)",
        "Ξ Ethereum (ETH)": "Ξ Ethereum (ETH)",
        "₮ Tether (USDT)": "₮ Tether (USDT)",
        "🔗 Chainlink (LINK)": "🔗 Chainlink (LINK)",
        "🪙 More Cryptos": "🪙 Daugiau kriptovaliutų",
        "« Back to Cart": "« Grįžti į krepšelį",
        "🔄 Refresh Status": "🔄 Atnaujinti statusą",
        "❓ Payment Help": "❓ Mokėjimo pagalba",
        "📞 Contact Support": "📞 Susisiekti su pagalba",
        "Check Payment Status": "Patikrinti mokėjimo statusą",
        "More Cryptocurrencies": "Daugiau kriptovaliutų",
        "Welcome to our crypto shop! 🛍️\n\nYou can browse our products, make purchases with cryptocurrency, and track your orders all from this bot.\n\nUse /menu to see available options or click the button below.": "Sveiki atvykę į mūsų kriptovaliutų parduotuvę! 🛍️\n\nGalite naršyti mūsų produktus, pirkti už kriptovaliutas ir sekti užsakymus šiame bote.\n\nNaudokite /menu norėdami pamatyti galimas parinktis arba spustelėkite mygtuką žemiau.",
    }
}


async def translate_text(text: str, language: str = "en") -> str:
    """
    Translate text to specified language.
    """
    try:
        if language in TRANSLATIONS and text in TRANSLATIONS[language]:
            return TRANSLATIONS[language][text]
        return text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text


async def get_or_create_user(telegram_user: TelegramUser) -> User:
    """
    Get existing user or create new one from Telegram user data.
    """
    db = SessionLocal()
    try:
        # Try to find existing user
        user = db.query(User).filter(
            User.telegram_id == str(telegram_user.id)
        ).first()
        
        if user:
            # Update user info if changed
            updated = False
            if user.username != telegram_user.username:
                user.username = telegram_user.username
                updated = True
            if user.first_name != telegram_user.first_name:
                user.first_name = telegram_user.first_name
                updated = True
            if user.last_name != telegram_user.last_name:
                user.last_name = telegram_user.last_name
                updated = True
            
            if updated:
                user.updated_at = datetime.now(timezone.utc)
                db.commit()
            
            return user
        
        # Create new user
        referral_code = generate_referral_code(telegram_user.id)
        
        user = User(
            telegram_id=str(telegram_user.id),
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language=telegram_user.language_code or "en",
            referral_code=referral_code,
            role=UserRole.CUSTOMER,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Created new user: {user.telegram_id}")
        return user
        
    except Exception as e:
        logger.error(f"Error getting/creating user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def generate_referral_code(telegram_id: int) -> str:
    """
    Generate unique referral code for user.
    """
    # Create a hash of telegram_id + timestamp
    data = f"{telegram_id}_{datetime.now().timestamp()}"
    hash_object = hashlib.md5(data.encode())
    return f"REF{hash_object.hexdigest()[:8].upper()}"


async def format_product_message(product: Product, language: str = "en") -> str:
    """
    Format product details message.
    """
    try:
        # Product title and price
        message = f"🛍️ <b>{product.name}</b>\n"
        message += f"💰 <b>${product.price:.2f}</b>"
        
        # Show compare price if different
        if product.compare_price and product.compare_price > product.price:
            savings = product.compare_price - product.price
            message += f" <s>${product.compare_price:.2f}</s>"
            message += f" (Save ${savings:.2f}!)"
        
        message += "\n\n"
        
        # Product description
        if product.description:
            message += f"📝 {product.description}\n\n"
        
        # Product type
        type_emoji = "💾" if product.product_type == ProductType.DIGITAL else "📦"
        product_type = "Digital" if product.product_type == ProductType.DIGITAL else "Physical"
        message += f"{type_emoji} <b>Type:</b> {product_type}\n"
        
        # Stock information
        if product.track_inventory:
            if product.stock_quantity > 0:
                if product.stock_quantity <= product.low_stock_threshold:
                    message += f"⚠️ <b>Stock:</b> Only {product.stock_quantity} left!\n"
                else:
                    message += f"✅ <b>Stock:</b> {product.stock_quantity} available\n"
            else:
                message += f"❌ <b>Stock:</b> Out of stock\n"
        else:
            message += f"♾️ <b>Stock:</b> Unlimited\n"
        
        # SKU
        if product.sku:
            message += f"🔖 <b>SKU:</b> {product.sku}\n"
        
        # Views
        if product.view_count > 0:
            message += f"👁️ <b>Views:</b> {product.view_count}\n"
        
        # Purchase count
        if product.purchase_count > 0:
            message += f"🛒 <b>Sold:</b> {product.purchase_count} times\n"
        
        # Digital product specific info
        if product.product_type == ProductType.DIGITAL:
            if product.download_limit:
                message += f"📥 <b>Download limit:</b> {product.download_limit}\n"
            if product.download_expiry_days:
                message += f"⏰ <b>Download expires:</b> {product.download_expiry_days} days\n"
        
        # Physical product specific info
        if product.product_type == ProductType.PHYSICAL:
            if product.weight:
                message += f"⚖️ <b>Weight:</b> {product.weight}kg\n"
            if all([product.length, product.width, product.height]):
                message += f"📏 <b>Dimensions:</b> {product.length}×{product.width}×{product.height}cm\n"
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting product message: {e}")
        return f"🛍️ <b>{product.name}</b>\n💰 <b>${product.price:.2f}</b>"


async def format_order_message(order: Order, language: str = "en") -> str:
    """
    Format order details message.
    """
    try:
        message = f"📦 <b>Order #{order.order_number}</b>\n\n"
        
        # Order status
        status_emoji = {
            "pending": "⏳",
            "paid": "💰",
            "processing": "🔄",
            "shipped": "🚚",
            "delivered": "✅",
            "cancelled": "❌",
            "refunded": "💸"
        }
        
        emoji = status_emoji.get(order.status.value, "📦")
        message += f"{emoji} <b>Status:</b> {order.status.value.title()}\n"
        
        # Order date
        message += f"📅 <b>Date:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        # Payment information
        message += f"💳 <b>Payment:</b> {order.payment_method or 'Cryptocurrency'}\n"
        message += f"💰 <b>Total:</b> ${order.total_amount:.2f} {order.currency}\n\n"
        
        # Order items
        message += "<b>Items:</b>\n"
        for item in order.items:
            message += f"• {item.product_name}\n"
            message += f"  Qty: {item.quantity} × ${item.unit_price:.2f} = ${item.total_price:.2f}\n"
        
        # Subtotal and fees
        message += f"\n<b>Subtotal:</b> ${order.subtotal:.2f}\n"
        
        if order.discount_amount > 0:
            message += f"<b>Discount:</b> -${order.discount_amount:.2f}\n"
        
        if order.tax_amount > 0:
            message += f"<b>Tax:</b> ${order.tax_amount:.2f}\n"
        
        if order.shipping_amount > 0:
            message += f"<b>Shipping:</b> ${order.shipping_amount:.2f}\n"
        
        message += f"<b>Total:</b> ${order.total_amount:.2f}\n"
        
        # Shipping information
        if order.shipping_address:
            message += f"\n📍 <b>Shipping Address:</b>\n"
            addr = order.shipping_address
            if isinstance(addr, dict):
                message += f"{addr.get('street', '')}\n"
                message += f"{addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}\n"
                message += f"{addr.get('country', '')}\n"
        
        # Tracking information
        if order.tracking_number:
            message += f"\n📦 <b>Tracking:</b> {order.tracking_number}\n"
        
        # Customer notes
        if order.customer_notes:
            message += f"\n📝 <b>Notes:</b> {order.customer_notes}\n"
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting order message: {e}")
        return f"📦 Order #{order.order_number}\n💰 ${order.total_amount:.2f}"


def calculate_order_total(items: List[Dict[str, Any]], discount_code: Optional[str] = None) -> Dict[str, float]:
    """
    Calculate order totals including discounts, tax, and shipping.
    """
    try:
        subtotal = sum(item["price"] * item["quantity"] for item in items)
        discount_amount = 0.0
        tax_amount = 0.0
        shipping_amount = 0.0
        
        # Apply discount code
        if discount_code:
            discount_amount = calculate_discount(subtotal, discount_code)
        
        # Calculate tax (implement based on business rules)
        taxable_amount = subtotal - discount_amount
        tax_rate = 0.0  # Set based on location/product type
        tax_amount = taxable_amount * tax_rate
        
        # Calculate shipping (implement based on business rules)
        has_physical_items = any(item.get("requires_shipping", False) for item in items)
        if has_physical_items:
            shipping_amount = calculate_shipping(items)
        
        total_amount = subtotal - discount_amount + tax_amount + shipping_amount
        
        return {
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "tax_amount": tax_amount,
            "shipping_amount": shipping_amount,
            "total_amount": total_amount
        }
        
    except Exception as e:
        logger.error(f"Error calculating order total: {e}")
        return {
            "subtotal": 0.0,
            "discount_amount": 0.0,
            "tax_amount": 0.0,
            "shipping_amount": 0.0,
            "total_amount": 0.0
        }


def calculate_discount(subtotal: float, discount_code: str) -> float:
    """
    Calculate discount amount based on discount code.
    """
    try:
        db = SessionLocal()
        try:
            from database.models import DiscountCode
            
            discount = db.query(DiscountCode).filter(
                DiscountCode.code == discount_code.upper(),
                DiscountCode.is_active == True
            ).first()
            
            if not discount:
                return 0.0
            
            # Check validity dates
            now = datetime.now(timezone.utc)
            if discount.valid_from and now < discount.valid_from:
                return 0.0
            if discount.valid_until and now > discount.valid_until:
                return 0.0
            
            # Check minimum amount
            if discount.minimum_amount and subtotal < discount.minimum_amount:
                return 0.0
            
            # Check usage limits
            if discount.usage_limit and discount.current_usage >= discount.usage_limit:
                return 0.0
            
            # Calculate discount
            if discount.type == "percentage":
                discount_amount = subtotal * (discount.value / 100)
            elif discount.type == "fixed_amount":
                discount_amount = discount.value
            else:
                return 0.0
            
            # Apply maximum discount limit
            if discount.maximum_amount:
                discount_amount = min(discount_amount, discount.maximum_amount)
            
            return min(discount_amount, subtotal)  # Don't exceed subtotal
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error calculating discount: {e}")
        return 0.0


def calculate_shipping(items: List[Dict[str, Any]]) -> float:
    """
    Calculate shipping cost based on items.
    """
    try:
        # Simple shipping calculation - implement based on business rules
        total_weight = sum(item.get("weight", 0) * item["quantity"] for item in items)
        
        if total_weight <= 0:
            return 0.0
        elif total_weight <= 1:
            return 5.0
        elif total_weight <= 5:
            return 10.0
        else:
            return 15.0
            
    except Exception as e:
        logger.error(f"Error calculating shipping: {e}")
        return 0.0


def get_user_language(user: User) -> str:
    """
    Get user's preferred language.
    """
    return user.language if user.language in settings.supported_languages else settings.default_language


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format currency amount for display.
    """
    try:
        if currency.upper() == "USD":
            return f"${amount:.2f}"
        else:
            return f"{amount:.2f} {currency.upper()}"
    except Exception:
        return f"{amount:.2f}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    """
    try:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    except Exception:
        return "Unknown size"


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_order_number() -> str:
    """
    Generate unique order number.
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    random_part = uuid.uuid4().hex[:6].upper()
    return f"ORD-{timestamp}-{random_part}"


def parse_callback_data(callback_data: str) -> Dict[str, str]:
    """
    Parse callback data into components.
    """
    try:
        parts = callback_data.split("_")
        if len(parts) >= 2:
            return {
                "action": parts[0],
                "type": parts[1],
                "params": parts[2:] if len(parts) > 2 else []
            }
        return {"action": callback_data, "type": "", "params": []}
    except Exception:
        return {"action": callback_data, "type": "", "params": []}


async def log_user_activity(user: User, action: str, details: Optional[Dict[str, Any]] = None):
    """
    Log user activity for analytics.
    """
    try:
        from database.models import ActivityLog
        
        db = SessionLocal()
        try:
            activity = ActivityLog(
                user_id=user.id,
                action=action,
                details=details or {},
                created_at=datetime.now(timezone.utc)
            )
            db.add(activity)
            db.commit()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")


def escape_html(text: str) -> str:
    """
    Escape HTML special characters for Telegram messages.
    """
    try:
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))
    except Exception:
        return str(text)


def format_datetime(dt: datetime, language: str = "en") -> str:
    """
    Format datetime for display in user's language.
    """
    try:
        if language == "lt":
            return dt.strftime("%Y-%m-%d %H:%M")
        else:
            return dt.strftime("%m/%d/%Y %I:%M %p")
    except Exception:
        return str(dt)