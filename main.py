"""
Main application entry point for the Telegram Shop Bot.

This module starts both the Telegram bot and the web admin panel,
handling all initialization and providing a comprehensive 24/7 shop bot solution.
"""
import asyncio
import signal
import sys
import threading
from pathlib import Path

import uvicorn
from loguru import logger

from config.settings import get_settings
from database.database import init_db
from bot.bot import telegram_bot
from web.app import app as web_app

settings = get_settings()

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)

# Add file logging
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

logger.add(
    "logs/shopbot_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)


class ShopBotApplication:
    """Main application class that manages both bot and web server."""
    
    def __init__(self):
        self.running = False
        self.web_server = None
        self.bot_task = None
        
    async def start(self):
        """Start the application."""
        try:
            logger.info("🚀 Starting Telegram Shop Bot Application")
            
            # Initialize database
            logger.info("📊 Initializing database...")
            init_db()
            
            # Create necessary directories
            self._create_directories()
            
            # Start both bot and web server
            await self._start_services()
            
            self.running = True
            logger.info("✅ Application started successfully")
            
            # Keep running
            await self._run_forever()
            
        except Exception as e:
            logger.error(f"❌ Failed to start application: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the application."""
        try:
            logger.info("🛑 Stopping Telegram Shop Bot Application")
            self.running = False
            
            # Stop bot
            if self.bot_task and not self.bot_task.done():
                logger.info("🤖 Stopping Telegram bot...")
                await telegram_bot.stop()
                self.bot_task.cancel()
                try:
                    await self.bot_task
                except asyncio.CancelledError:
                    pass
            
            # Stop web server
            if self.web_server:
                logger.info("🌐 Stopping web server...")
                self.web_server.should_exit = True
            
            logger.info("✅ Application stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping application: {e}")
    
    def _create_directories(self):
        """Create necessary directories."""
        directories = [
            "logs",
            "exports", 
            "uploads",
            "backups",
            "web/static",
            "web/templates"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
        logger.info("📁 Created necessary directories")
    
    async def _start_services(self):
        """Start both Telegram bot and web server."""
        # Start Telegram bot
        logger.info("🤖 Starting Telegram bot...")
        self.bot_task = asyncio.create_task(self._run_bot())
        
        # Start web server
        logger.info("🌐 Starting web admin panel...")
        await self._start_web_server()
    
    async def _run_bot(self):
        """Run the Telegram bot."""
        try:
            await telegram_bot.start()
            
            # If using webhooks, bot will handle via web server
            if not settings.webhook_url:
                # Keep bot running with polling
                await telegram_bot.application.updater.idle()
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise
    
    async def _start_web_server(self):
        """Start the web server."""
        try:
            # Configure uvicorn
            config = uvicorn.Config(
                app=web_app,
                host="0.0.0.0",
                port=8000,
                log_level=settings.log_level.lower(),
                access_log=True,
                reload=settings.debug,
                workers=1 if settings.debug else 4
            )
            
            self.web_server = uvicorn.Server(config)
            
            # Start server in background
            def run_server():
                asyncio.run(self.web_server.serve())
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            logger.info(f"🌐 Web admin panel available at http://localhost:8000")
            
        except Exception as e:
            logger.error(f"Web server error: {e}")
            raise
    
    async def _run_forever(self):
        """Keep the application running."""
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("👋 Received shutdown signal")
        except Exception as e:
            logger.error(f"Runtime error: {e}")
        finally:
            await self.stop()


async def main():
    """Main function."""
    app = ShopBotApplication()
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(app.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("👋 Application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        sys.exit(1)


def run_development():
    """Run in development mode with auto-reload."""
    logger.info("🔧 Starting in development mode")
    
    # Run web server with auto-reload
    uvicorn.run(
        "web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True
    )


def run_production():
    """Run in production mode."""
    logger.info("🚀 Starting in production mode")
    asyncio.run(main())


def create_admin():
    """Create admin user via command line."""
    import getpass
    from web.auth import create_admin_user
    from database.models import UserRole
    
    print("🔐 Creating admin user")
    
    username = input("Username: ")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    
    try:
        user = create_admin_user(username, email, password, UserRole.ADMIN)
        print(f"✅ Admin user '{username}' created successfully!")
        print(f"   Email: {email}")
        print(f"   Role: {user.role.value}")
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")


def setup_database():
    """Initialize database tables."""
    logger.info("📊 Setting up database...")
    init_db()
    logger.info("✅ Database setup complete")


def backup_database():
    """Create database backup."""
    from web.utils import create_backup
    
    logger.info("💾 Creating database backup...")
    try:
        asyncio.run(create_backup())
        logger.info("✅ Database backup created successfully")
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")


def show_help():
    """Show help information."""
    print("""
🤖 Telegram Shop Bot - Comprehensive E-commerce Solution

Usage: python main.py [command]

Commands:
  run                 Start the full application (bot + web panel)
  dev                 Start in development mode with auto-reload
  create-admin        Create admin user via command line
  setup-db           Initialize database tables
  backup             Create database backup
  help               Show this help message

Examples:
  python main.py run              # Start production server
  python main.py dev              # Start development server
  python main.py create-admin     # Create admin user
  python main.py setup-db         # Initialize database

Features:
  ✅ 24/7 Telegram bot operation
  ✅ Crypto payments via NOWPayments
  ✅ QR code payment invoices
  ✅ Web admin panel with analytics
  ✅ Multi-language support (EN/LT)
  ✅ Inventory management
  ✅ Order tracking
  ✅ Customer support system
  ✅ Referral/affiliate program
  ✅ Automated backups
  ✅ Security (2FA, encryption)
  ✅ Sales reports & analytics

For more information, visit: https://github.com/your-repo/tg-shop-bot
    """)


if __name__ == "__main__":
    """Entry point when running directly."""
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "run":
            run_production()
        elif command == "dev":
            run_development()
        elif command == "create-admin":
            create_admin()
        elif command == "setup-db":
            setup_database()
        elif command == "backup":
            backup_database()
        elif command == "help":
            show_help()
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python main.py help' for available commands")
            sys.exit(1)
    else:
        # Default: run production
        run_production()
