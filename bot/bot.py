"""
Main Telegram Shop Bot implementation.
"""
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
from loguru import logger

from config.settings import get_settings
from database.database import SessionLocal, get_db
from database.models import (
    User, Product, Category, Order, OrderItem, Payment,
    UserRole, OrderStatus, PaymentStatus, ProductType
)
from services.nowpayments import nowpayments_service
from services.qr_generator import qr_generator
from .keyboards import (
    main_menu_keyboard, category_keyboard, product_keyboard,
    cart_keyboard, payment_keyboard, order_history_keyboard
)
from .utils import (
    get_or_create_user, format_product_message, format_order_message,
    calculate_order_total, get_user_language, translate_text
)

settings = get_settings()

# Conversation states
(SELECTING_CATEGORY, SELECTING_PRODUCT, VIEWING_PRODUCT, 
 ADDING_TO_CART, CHECKOUT, PAYMENT_METHOD, PAYMENT_CONFIRMATION,
 SUPPORT_MESSAGE, SUPPORT_CATEGORY) = range(9)


class TelegramShopBot:
    """Main Telegram shop bot class."""
    
    def __init__(self):
        self.application = None
        self.user_carts = {}  # In-memory cart storage (use Redis in production)
        self.user_states = {}  # User conversation states
        
    async def initialize(self):
        """Initialize the bot application."""
        try:
            # Create application
            self.application = Application.builder().token(
                settings.telegram_bot_token
            ).build()
            
            # Add handlers
            self._add_handlers()
            
            logger.info("Telegram bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            raise
    
    async def start(self):
        """Start the bot."""
        try:
            if not self.application:
                await self.initialize()
            
            logger.info("Starting Telegram bot...")
            await self.application.initialize()
            await self.application.start()
            
            # Set webhook if configured
            if settings.webhook_url:
                webhook_url = f"{settings.webhook_url}/webhook"
                await self.application.bot.set_webhook(webhook_url)
                logger.info(f"Webhook set to: {webhook_url}")
            else:
                # Start polling
                await self.application.updater.start_polling()
                logger.info("Bot started with polling")
            
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot."""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram bot stopped")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    def _add_handlers(self):
        """Add all command and message handlers."""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("cart", self.cart_command))
        self.application.add_handler(CommandHandler("orders", self.orders_command))
        self.application.add_handler(CommandHandler("support", self.support_command))
        self.application.add_handler(CommandHandler("language", self.language_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(
            self.handle_category_selection, pattern="^category_"
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.handle_product_selection, pattern="^product_"
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.handle_cart_action, pattern="^cart_"
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.handle_payment_action, pattern="^payment_"
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.handle_order_action, pattern="^order_"
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.handle_support_action, pattern="^support_"
        ))
        
        # Conversation handler for support
        support_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.start_support, pattern="^support_new$"
            )],
            states={
                SUPPORT_CATEGORY: [CallbackQueryHandler(
                    self.support_category_selected, pattern="^support_cat_"
                )],
                SUPPORT_MESSAGE: [MessageHandler(
                    filters.TEXT & ~filters.COMMAND, self.support_message_received
                )],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_support)],
        )
        self.application.add_handler(support_conv)
        
        # Message handlers
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.handle_text_message
        ))
        self.application.add_handler(MessageHandler(
            filters.PHOTO, self.handle_photo_message
        ))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        try:
            user = update.effective_user
            telegram_user = await get_or_create_user(user)
            
            welcome_message = await translate_text(
                "Welcome to our crypto shop! 🛍️\n\n"
                "You can browse our products, make purchases with cryptocurrency, "
                "and track your orders all from this bot.\n\n"
                "Use /menu to see available options or click the button below.",
                telegram_user.language
            )
            
            keyboard = main_menu_keyboard(telegram_user.language)
            
            await update.message.reply_text(
                welcome_message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("Sorry, an error occurred. Please try again.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        try:
            user = update.effective_user
            telegram_user = await get_or_create_user(user)
            
            help_text = await translate_text(
                "🤖 <b>Shop Bot Help</b>\n\n"
                "<b>Commands:</b>\n"
                "/start - Start the bot and see welcome message\n"
                "/menu - Show main menu\n"
                "/cart - View your shopping cart\n"
                "/orders - View your order history\n"
                "/support - Contact customer support\n"
                "/language - Change language\n"
                "/profile - View your profile\n\n"
                "<b>How to shop:</b>\n"
                "1. Browse categories and products\n"
                "2. Add items to your cart\n"
                "3. Proceed to checkout\n"
                "4. Pay with cryptocurrency\n"
                "5. Receive your digital products instantly\n\n"
                "<b>Payment:</b>\n"
                "We accept various cryptocurrencies including Bitcoin, Ethereum, "
                "and many others. All payments are processed securely.\n\n"
                "<b>Support:</b>\n"
                "Need help? Use /support to contact our customer service team.",
                telegram_user.language
            )
            
            await update.message.reply_text(
                help_text,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await update.message.reply_text("Sorry, an error occurred. Please try again.")
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command."""
        try:
            user = update.effective_user
            telegram_user = await get_or_create_user(user)
            
            menu_text = await translate_text(
                "🛍️ <b>Main Menu</b>\n\nWhat would you like to do?",
                telegram_user.language
            )
            
            keyboard = main_menu_keyboard(telegram_user.language)
            
            await update.message.reply_text(
                menu_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error in menu command: {e}")
            await update.message.reply_text("Sorry, an error occurred. Please try again.")
    
    async def cart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cart command."""
        try:
            user = update.effective_user
            telegram_user = await get_or_create_user(user)
            cart = self.user_carts.get(user.id, {})
            
            if not cart:
                empty_message = await translate_text(
                    "🛒 Your cart is empty.\n\nBrowse our products to add items!",
                    telegram_user.language
                )
                await update.message.reply_text(empty_message)
                return
            
            # Calculate cart total
            db = SessionLocal()
            try:
                total_amount = 0
                cart_text = await translate_text("🛒 <b>Your Cart</b>\n\n", telegram_user.language)
                
                for product_id, quantity in cart.items():
                    product = db.query(Product).filter(Product.id == product_id).first()
                    if product:
                        item_total = product.price * quantity
                        total_amount += item_total
                        
                        cart_text += f"• {product.name}\n"
                        cart_text += f"  ${product.price:.2f} x {quantity} = ${item_total:.2f}\n\n"
                
                cart_text += f"<b>Total: ${total_amount:.2f}</b>"
                
                keyboard = cart_keyboard(telegram_user.language)
                
                await update.message.reply_text(
                    cart_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in cart command: {e}")
            await update.message.reply_text("Sorry, an error occurred. Please try again.")
    
    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /orders command."""
        try:
            user = update.effective_user
            telegram_user = await get_or_create_user(user)
            
            db = SessionLocal()
            try:
                orders = db.query(Order).filter(
                    Order.user_id == telegram_user.id
                ).order_by(Order.created_at.desc()).limit(10).all()
                
                if not orders:
                    no_orders = await translate_text(
                        "📦 You haven't placed any orders yet.\n\nStart shopping to see your orders here!",
                        telegram_user.language
                    )
                    await update.message.reply_text(no_orders)
                    return
                
                orders_text = await translate_text("📦 <b>Your Recent Orders</b>\n\n", telegram_user.language)
                
                for order in orders:
                    status_emoji = "⏳" if order.status == OrderStatus.PENDING else "✅"
                    orders_text += f"{status_emoji} Order #{order.order_number}\n"
                    orders_text += f"Amount: ${order.total_amount:.2f}\n"
                    orders_text += f"Status: {order.status.value.title()}\n"
                    orders_text += f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                
                keyboard = order_history_keyboard(telegram_user.language)
                
                await update.message.reply_text(
                    orders_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in orders command: {e}")
            await update.message.reply_text("Sorry, an error occurred. Please try again.")
    
    async def handle_category_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle category selection."""
        try:
            query = update.callback_query
            await query.answer()
            
            category_id = int(query.data.split("_")[1])
            user = update.effective_user
            telegram_user = await get_or_create_user(user)
            
            db = SessionLocal()
            try:
                category = db.query(Category).filter(Category.id == category_id).first()
                if not category:
                    await query.edit_message_text("Category not found.")
                    return
                
                products = db.query(Product).filter(
                    Product.category_id == category_id,
                    Product.is_active == True
                ).all()
                
                if not products:
                    no_products = await translate_text(
                        f"No products available in {category.name} category.",
                        telegram_user.language
                    )
                    await query.edit_message_text(no_products)
                    return
                
                category_text = await translate_text(
                    f"🏷️ <b>{category.name}</b>\n\n{category.description or ''}\n\nSelect a product:",
                    telegram_user.language
                )
                
                keyboard = []
                for product in products:
                    keyboard.append([InlineKeyboardButton(
                        f"{product.name} - ${product.price:.2f}",
                        callback_data=f"product_{product.id}"
                    )])
                
                keyboard.append([InlineKeyboardButton(
                    await translate_text("« Back to Categories", telegram_user.language),
                    callback_data="back_to_categories"
                )])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    category_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error handling category selection: {e}")
            await query.edit_message_text("Sorry, an error occurred. Please try again.")
    
    async def handle_product_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle product selection."""
        try:
            query = update.callback_query
            await query.answer()
            
            product_id = int(query.data.split("_")[1])
            user = update.effective_user
            telegram_user = await get_or_create_user(user)
            
            db = SessionLocal()
            try:
                product = db.query(Product).filter(Product.id == product_id).first()
                if not product:
                    await query.edit_message_text("Product not found.")
                    return
                
                # Update view count
                product.view_count += 1
                db.commit()
                
                product_text = await format_product_message(product, telegram_user.language)
                keyboard = product_keyboard(product, telegram_user.language)
                
                # Send product image if available
                if product.images and len(product.images) > 0:
                    await query.message.reply_photo(
                        photo=product.images[0],
                        caption=product_text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                    await query.delete_message()
                else:
                    await query.edit_message_text(
                        product_text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error handling product selection: {e}")
            await query.edit_message_text("Sorry, an error occurred. Please try again.")
    
    async def handle_cart_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle cart actions (add, remove, checkout)."""
        try:
            query = update.callback_query
            await query.answer()
            
            action_data = query.data.split("_")
            action = action_data[1]
            
            user = update.effective_user
            telegram_user = await get_or_create_user(user)
            
            if action == "add":
                product_id = int(action_data[2])
                quantity = int(action_data[3]) if len(action_data) > 3 else 1
                
                # Add to cart
                if user.id not in self.user_carts:
                    self.user_carts[user.id] = {}
                
                self.user_carts[user.id][product_id] = (
                    self.user_carts[user.id].get(product_id, 0) + quantity
                )
                
                success_message = await translate_text(
                    f"✅ Product added to cart! Quantity: {quantity}",
                    telegram_user.language
                )
                await query.answer(success_message, show_alert=True)
                
            elif action == "checkout":
                await self.start_checkout(query, telegram_user)
                
        except Exception as e:
            logger.error(f"Error handling cart action: {e}")
            await query.answer("Sorry, an error occurred.", show_alert=True)
    
    async def start_checkout(self, query, telegram_user):
        """Start the checkout process."""
        try:
            cart = self.user_carts.get(telegram_user.telegram_id, {})
            if not cart:
                empty_cart = await translate_text(
                    "Your cart is empty. Add some products first!",
                    telegram_user.language
                )
                await query.answer(empty_cart, show_alert=True)
                return
            
            db = SessionLocal()
            try:
                # Create order
                order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
                
                # Calculate totals
                subtotal = 0
                order_items = []
                
                for product_id, quantity in cart.items():
                    product = db.query(Product).filter(Product.id == product_id).first()
                    if product:
                        item_total = product.price * quantity
                        subtotal += item_total
                        order_items.append({
                            "product": product,
                            "quantity": quantity,
                            "unit_price": product.price,
                            "total_price": item_total
                        })
                
                # Create order
                order = Order(
                    order_number=order_number,
                    user_id=telegram_user.id,
                    status=OrderStatus.PENDING,
                    subtotal=subtotal,
                    total_amount=subtotal,  # TODO: Add tax and shipping
                    currency="USD"
                )
                
                db.add(order)
                db.flush()  # Get the order ID
                
                # Create order items
                for item_data in order_items:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item_data["product"].id,
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        total_price=item_data["total_price"],
                        product_name=item_data["product"].name,
                        product_sku=item_data["product"].sku
                    )
                    db.add(order_item)
                
                db.commit()
                
                # Clear cart
                if telegram_user.telegram_id in self.user_carts:
                    del self.user_carts[telegram_user.telegram_id]
                
                # Show payment options
                await self.show_payment_options(query, order, telegram_user)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in checkout: {e}")
            await query.answer("Checkout failed. Please try again.", show_alert=True)
    
    async def show_payment_options(self, query, order, telegram_user):
        """Show available payment options."""
        try:
            # Get available cryptocurrencies
            currencies = await nowpayments_service.get_available_currencies()
            
            payment_text = await translate_text(
                f"💳 <b>Payment for Order #{order.order_number}</b>\n\n"
                f"Total Amount: ${order.total_amount:.2f}\n\n"
                f"Select your preferred cryptocurrency:",
                telegram_user.language
            )
            
            keyboard = []
            
            # Popular cryptocurrencies first
            popular_currencies = ["btc", "eth", "usdt", "bnb", "ada", "dot"]
            
            for currency in popular_currencies:
                if currency in currencies:
                    keyboard.append([InlineKeyboardButton(
                        currency.upper(),
                        callback_data=f"payment_crypto_{order.id}_{currency}"
                    )])
            
            # Add "More Options" button
            keyboard.append([InlineKeyboardButton(
                await translate_text("More Cryptocurrencies", telegram_user.language),
                callback_data=f"payment_more_{order.id}"
            )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                payment_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error showing payment options: {e}")
            await query.edit_message_text("Failed to load payment options.")
    
    async def handle_payment_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment actions."""
        try:
            query = update.callback_query
            await query.answer()
            
            action_data = query.data.split("_")
            action = action_data[1]
            
            user = update.effective_user
            telegram_user = await get_or_create_user(user)
            
            if action == "crypto":
                order_id = int(action_data[2])
                currency = action_data[3]
                
                await self.process_crypto_payment(query, order_id, currency, telegram_user)
                
        except Exception as e:
            logger.error(f"Error handling payment action: {e}")
            await query.answer("Payment error. Please try again.", show_alert=True)
    
    async def process_crypto_payment(self, query, order_id, currency, telegram_user):
        """Process cryptocurrency payment."""
        try:
            db = SessionLocal()
            try:
                order = db.query(Order).filter(Order.id == order_id).first()
                if not order:
                    await query.edit_message_text("Order not found.")
                    return
                
                # Create payment with NOWPayments
                payment_data = await nowpayments_service.create_payment(
                    order=order,
                    pay_currency=currency,
                    order_description=f"Order {order.order_number}"
                )
                
                if not payment_data:
                    await query.edit_message_text("Failed to create payment. Please try again.")
                    return
                
                # Save payment to database
                payment = Payment(
                    order_id=order.id,
                    payment_id=payment_data.get("payment_id"),
                    payment_status=PaymentStatus.WAITING,
                    pay_address=payment_data.get("pay_address"),
                    price_amount=order.total_amount,
                    price_currency=order.currency,
                    pay_amount=payment_data.get("pay_amount"),
                    pay_currency=currency.upper(),
                    purchase_id=payment_data.get("purchase_id"),
                    expires_at=datetime.now(timezone.utc)
                )
                
                db.add(payment)
                db.commit()
                
                # Generate QR code
                qr_data = await nowpayments_service.create_qr_payment_data(payment_data)
                qr_info = qr_generator.create_payment_qr_data(
                    payment_uri=qr_data.get("qr_data", ""),
                    amount=str(payment_data.get("pay_amount", "")),
                    currency=currency.upper(),
                    address=payment_data.get("pay_address", "")
                )
                
                # Send payment instructions with QR code
                payment_text = await translate_text(
                    f"💰 <b>Payment Instructions</b>\n\n"
                    f"Order: #{order.order_number}\n"
                    f"Amount to pay: {payment_data.get('pay_amount')} {currency.upper()}\n"
                    f"Address: <code>{payment_data.get('pay_address')}</code>\n\n"
                    f"Please send the exact amount to the address above.\n"
                    f"Payment will be automatically confirmed.",
                    telegram_user.language
                )
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        await translate_text("Check Payment Status", telegram_user.language),
                        callback_data=f"payment_status_{payment.id}"
                    )
                ]])
                
                if qr_info.get("qr_code_bytes"):
                    await query.message.reply_photo(
                        photo=qr_info["qr_code_bytes"],
                        caption=payment_text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                    await query.delete_message()
                else:
                    await query.edit_message_text(
                        payment_text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing crypto payment: {e}")
            await query.edit_message_text("Payment processing failed. Please try again.")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Update {update} caused error {context.error}")
        
        try:
            if update.effective_message:
                await update.effective_message.reply_text(
                    "Sorry, an unexpected error occurred. Please try again later."
                )
        except Exception:
            pass
    
    # Additional handler methods would go here...
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages."""
        # Implement based on user state and message content
        pass
    
    async def handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages (for support tickets)."""
        # Implement photo handling for support
        pass
    
    async def support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle support command."""
        # Implement support ticket creation
        pass
    
    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language change command."""
        # Implement language switching
        pass
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle profile command."""
        # Implement user profile display
        pass
    
    # Support conversation handlers
    async def start_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start support conversation."""
        return SUPPORT_CATEGORY
    
    async def support_category_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle support category selection."""
        return SUPPORT_MESSAGE
    
    async def support_message_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle support message."""
        return ConversationHandler.END
    
    async def cancel_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel support conversation."""
        return ConversationHandler.END
    
    async def handle_support_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle support-related callback queries."""
        pass
    
    async def handle_order_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle order-related callback queries."""
        pass


# Global bot instance
telegram_bot = TelegramShopBot()