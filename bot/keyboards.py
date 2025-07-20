"""
Keyboard layouts for the Telegram shop bot.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Optional
from database.models import Product, Category
from .utils import translate_text


async def main_menu_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Create main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("🛍️ Browse Products", language),
                callback_data="browse_products"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🛒 My Cart", language),
                callback_data="view_cart"
            ),
            InlineKeyboardButton(
                await translate_text("📦 My Orders", language),
                callback_data="view_orders"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("👤 Profile", language),
                callback_data="view_profile"
            ),
            InlineKeyboardButton(
                await translate_text("🎁 Referrals", language),
                callback_data="referral_program"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🎯 Promotions", language),
                callback_data="view_promotions"
            ),
            InlineKeyboardButton(
                await translate_text("💡 Support", language),
                callback_data="support_menu"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🌐 Language", language),
                callback_data="change_language"
            ),
            InlineKeyboardButton(
                await translate_text("ℹ️ Help", language),
                callback_data="show_help"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def category_keyboard(categories: List[Category], language: str = "en") -> InlineKeyboardMarkup:
    """Create category selection keyboard."""
    keyboard = []
    
    # Add categories in rows of 2
    for i in range(0, len(categories), 2):
        row = []
        for j in range(2):
            if i + j < len(categories):
                category = categories[i + j]
                row.append(InlineKeyboardButton(
                    f"🏷️ {category.name}",
                    callback_data=f"category_{category.id}"
                ))
        keyboard.append(row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            await translate_text("« Back to Menu", language),
            callback_data="back_to_menu"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)


async def product_keyboard(product: Product, language: str = "en") -> InlineKeyboardMarkup:
    """Create product details keyboard."""
    keyboard = []
    
    # Add to cart options
    if product.stock_quantity > 0 or not product.track_inventory:
        keyboard.extend([
            [
                InlineKeyboardButton(
                    await translate_text("➕ Add 1 to Cart", language),
                    callback_data=f"cart_add_{product.id}_1"
                )
            ],
            [
                InlineKeyboardButton(
                    await translate_text("🛒 Add 3 to Cart", language),
                    callback_data=f"cart_add_{product.id}_3"
                ),
                InlineKeyboardButton(
                    await translate_text("🛒 Add 5 to Cart", language),
                    callback_data=f"cart_add_{product.id}_5"
                )
            ]
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                await translate_text("❌ Out of Stock", language),
                callback_data="out_of_stock"
            )
        ])
    
    # Product actions
    keyboard.extend([
        [
            InlineKeyboardButton(
                await translate_text("📝 Reviews", language),
                callback_data=f"product_reviews_{product.id}"
            ),
            InlineKeyboardButton(
                await translate_text("📤 Share", language),
                callback_data=f"product_share_{product.id}"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Back to Category", language),
                callback_data=f"category_{product.category_id}"
            )
        ]
    ])
    
    return InlineKeyboardMarkup(keyboard)


async def cart_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Create cart management keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("💳 Checkout", language),
                callback_data="cart_checkout"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🗑️ Clear Cart", language),
                callback_data="cart_clear"
            ),
            InlineKeyboardButton(
                await translate_text("📝 Edit Items", language),
                callback_data="cart_edit"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🛍️ Continue Shopping", language),
                callback_data="browse_products"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Back to Menu", language),
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def payment_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Create payment method selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("₿ Bitcoin (BTC)", language),
                callback_data="payment_crypto_btc"
            ),
            InlineKeyboardButton(
                await translate_text("Ξ Ethereum (ETH)", language),
                callback_data="payment_crypto_eth"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("₮ Tether (USDT)", language),
                callback_data="payment_crypto_usdt"
            ),
            InlineKeyboardButton(
                await translate_text("🔗 Chainlink (LINK)", language),
                callback_data="payment_crypto_link"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🪙 More Cryptos", language),
                callback_data="payment_more_cryptos"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Back to Cart", language),
                callback_data="view_cart"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def payment_status_keyboard(payment_id: int, language: str = "en") -> InlineKeyboardMarkup:
    """Create payment status check keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("🔄 Refresh Status", language),
                callback_data=f"payment_status_{payment_id}"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("❓ Payment Help", language),
                callback_data=f"payment_help_{payment_id}"
            ),
            InlineKeyboardButton(
                await translate_text("📞 Contact Support", language),
                callback_data="support_payment"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("📦 My Orders", language),
                callback_data="view_orders"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def order_history_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Create order history keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("🔍 Filter Orders", language),
                callback_data="orders_filter"
            ),
            InlineKeyboardButton(
                await translate_text("📊 Export History", language),
                callback_data="orders_export"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🔄 Refresh", language),
                callback_data="orders_refresh"
            ),
            InlineKeyboardButton(
                await translate_text("📧 Email Receipt", language),
                callback_data="orders_email"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🛍️ Shop Again", language),
                callback_data="browse_products"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Back to Menu", language),
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def order_details_keyboard(order_id: int, language: str = "en") -> InlineKeyboardMarkup:
    """Create order details keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("📋 Order Details", language),
                callback_data=f"order_details_{order_id}"
            ),
            InlineKeyboardButton(
                await translate_text("📦 Track Order", language),
                callback_data=f"order_track_{order_id}"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("📥 Download Items", language),
                callback_data=f"order_download_{order_id}"
            ),
            InlineKeyboardButton(
                await translate_text("🔄 Reorder", language),
                callback_data=f"order_reorder_{order_id}"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("📞 Support", language),
                callback_data=f"support_order_{order_id}"
            ),
            InlineKeyboardButton(
                await translate_text("📧 Email Receipt", language),
                callback_data=f"order_receipt_{order_id}"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Back to Orders", language),
                callback_data="view_orders"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def support_menu_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Create support menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("🎫 New Ticket", language),
                callback_data="support_new"
            ),
            InlineKeyboardButton(
                await translate_text("📋 My Tickets", language),
                callback_data="support_tickets"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("❓ FAQ", language),
                callback_data="support_faq"
            ),
            InlineKeyboardButton(
                await translate_text("📚 Help Center", language),
                callback_data="support_help"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("💬 Live Chat", language),
                callback_data="support_chat"
            ),
            InlineKeyboardButton(
                await translate_text("📧 Email Support", language),
                callback_data="support_email"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Back to Menu", language),
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def support_category_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Create support category selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("💳 Payment Issues", language),
                callback_data="support_cat_payment"
            ),
            InlineKeyboardButton(
                await translate_text("📦 Order Problems", language),
                callback_data="support_cat_order"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🔧 Technical Issues", language),
                callback_data="support_cat_technical"
            ),
            InlineKeyboardButton(
                await translate_text("🛍️ Product Questions", language),
                callback_data="support_cat_product"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🎁 Refunds & Returns", language),
                callback_data="support_cat_refund"
            ),
            InlineKeyboardButton(
                await translate_text("📋 Account Issues", language),
                callback_data="support_cat_account"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("❓ Other", language),
                callback_data="support_cat_other"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Cancel", language),
                callback_data="support_cancel"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def language_keyboard(current_language: str = "en") -> InlineKeyboardMarkup:
    """Create language selection keyboard."""
    languages = [
        ("🇺🇸 English", "en"),
        ("🇱🇹 Lietuvių", "lt"),
        ("🇪🇸 Español", "es"),
        ("🇫🇷 Français", "fr"),
        ("🇩🇪 Deutsch", "de"),
        ("🇷🇺 Русский", "ru")
    ]
    
    keyboard = []
    for i in range(0, len(languages), 2):
        row = []
        for j in range(2):
            if i + j < len(languages):
                name, code = languages[i + j]
                if code == current_language:
                    name += " ✓"
                row.append(InlineKeyboardButton(
                    name,
                    callback_data=f"language_{code}"
                ))
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton(
            "« Back to Menu",
            callback_data="back_to_menu"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)


async def profile_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Create user profile keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("✏️ Edit Profile", language),
                callback_data="profile_edit"
            ),
            InlineKeyboardButton(
                await translate_text("🔒 Security", language),
                callback_data="profile_security"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("💎 Loyalty Points", language),
                callback_data="profile_loyalty"
            ),
            InlineKeyboardButton(
                await translate_text("🎁 Referrals", language),
                callback_data="profile_referrals"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("📊 Statistics", language),
                callback_data="profile_stats"
            ),
            InlineKeyboardButton(
                await translate_text("📱 Notifications", language),
                callback_data="profile_notifications"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("🗑️ Delete Account", language),
                callback_data="profile_delete"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Back to Menu", language),
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def referral_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Create referral program keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("📋 My Referral Code", language),
                callback_data="referral_code"
            ),
            InlineKeyboardButton(
                await translate_text("📊 Referral Stats", language),
                callback_data="referral_stats"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("💰 Earnings", language),
                callback_data="referral_earnings"
            ),
            InlineKeyboardButton(
                await translate_text("👥 My Referrals", language),
                callback_data="referral_list"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("📤 Share Link", language),
                callback_data="referral_share"
            ),
            InlineKeyboardButton(
                await translate_text("ℹ️ How it Works", language),
                callback_data="referral_info"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Back to Menu", language),
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def promotions_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Create promotions keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("🎯 Active Promotions", language),
                callback_data="promotions_active"
            ),
            InlineKeyboardButton(
                await translate_text("🏷️ Discount Codes", language),
                callback_data="promotions_codes"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("⭐ Featured Deals", language),
                callback_data="promotions_featured"
            ),
            InlineKeyboardButton(
                await translate_text("🔥 Flash Sales", language),
                callback_data="promotions_flash"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("💎 VIP Offers", language),
                callback_data="promotions_vip"
            ),
            InlineKeyboardButton(
                await translate_text("🎁 Free Items", language),
                callback_data="promotions_free"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Back to Menu", language),
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def admin_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Create admin control keyboard (for admin users)."""
    keyboard = [
        [
            InlineKeyboardButton(
                await translate_text("📊 Analytics", language),
                callback_data="admin_analytics"
            ),
            InlineKeyboardButton(
                await translate_text("👥 Users", language),
                callback_data="admin_users"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("📦 Orders", language),
                callback_data="admin_orders"
            ),
            InlineKeyboardButton(
                await translate_text("🛍️ Products", language),
                callback_data="admin_products"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("💳 Payments", language),
                callback_data="admin_payments"
            ),
            InlineKeyboardButton(
                await translate_text("🎫 Support", language),
                callback_data="admin_support"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("⚙️ Settings", language),
                callback_data="admin_settings"
            ),
            InlineKeyboardButton(
                await translate_text("📱 Broadcast", language),
                callback_data="admin_broadcast"
            )
        ],
        [
            InlineKeyboardButton(
                await translate_text("« Exit Admin", language),
                callback_data="back_to_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# Quick reply keyboards for common actions
def quick_reply_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    """Create quick reply keyboard for common actions."""
    keyboard = [
        [
            KeyboardButton("🛍️ Shop"),
            KeyboardButton("🛒 Cart"),
            KeyboardButton("📦 Orders")
        ],
        [
            KeyboardButton("💡 Support"),
            KeyboardButton("👤 Profile"),
            KeyboardButton("ℹ️ Help")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )