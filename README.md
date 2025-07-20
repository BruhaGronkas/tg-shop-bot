# 🤖 Telegram Shop Bot - Complete E-commerce Solution

A comprehensive 24/7 Telegram shop bot with cryptocurrency payment support (NOWPayments API), instant QR code invoicing, and a robust web-based admin panel. Perfect for digital and physical product sales with multi-language support.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-blue.svg)](https://core.telegram.org/bots/api)
[![NOWPayments](https://img.shields.io/badge/NOWPayments-API-orange.svg)](https://nowpayments.io)

## ✨ Features

### 🛍️ Core Shop Features
- **24/7 Operation** - Continuous bot operation with automatic restarts
- **Product Catalog** - Intuitive browsing with categories and search
- **Shopping Cart** - Add/remove items with quantity management
- **Multi-language Support** - English and Lithuanian (easily extensible)
- **Digital & Physical Products** - Support for both product types

### 💰 Payment System
- **Cryptocurrency Payments** - Via NOWPayments API (50+ cryptocurrencies)
- **QR Code Invoices** - Instant payment QR codes with amount and address
- **Auto Payment Detection** - Real-time payment confirmation
- **Payment History** - Complete transaction tracking

### 🎯 Advanced Features
- **Loyalty Program** - Points system with rewards
- **Referral System** - Affiliate program with commissions
- **Discount Codes** - Flexible promotion system
- **Inventory Management** - Stock tracking with low-stock alerts
- **Order Tracking** - Complete order lifecycle management
- **Digital Delivery** - Automatic file delivery for digital products

### 🛡️ Security & Administration
- **Web Admin Panel** - Comprehensive management dashboard
- **Two-Factor Authentication** - TOTP-based 2FA for admin accounts
- **Role-Based Access** - Admin and moderator roles
- **Encrypted Storage** - Sensitive data encryption
- **Rate Limiting** - DDoS protection and abuse prevention
- **Activity Logging** - Complete audit trail

### 📊 Analytics & Reporting
- **Sales Analytics** - Revenue trends and conversion tracking
- **Customer Insights** - User behavior and retention metrics
- **Export Reports** - CSV, XLSX, and PDF exports
- **Inventory Reports** - Stock levels and bestsellers
- **Payment Analytics** - Transaction success rates and methods

### 🎫 Customer Support
- **Integrated Ticketing** - Support system within bot and web panel
- **Live Chat** - Real-time customer support
- **FAQ System** - Automated responses to common questions
- **Multilingual Support** - Support in multiple languages

### 🔄 Operations
- **Automated Backups** - Scheduled database backups
- **Data Recovery** - Backup restoration tools
- **System Monitoring** - Health checks and alerts
- **Scalable Architecture** - Modular design for easy scaling

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL or SQLite
- Redis (optional, for production caching)
- Telegram Bot Token
- NOWPayments API Key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-repo/tg-shop-bot.git
cd tg-shop-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Set up database**
```bash
python main.py setup-db
```

5. **Create admin user**
```bash
python main.py create-admin
```

6. **Start the application**
```bash
python main.py run
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
NOWPAYMENTS_API_KEY=your_nowpayments_api_key
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key-32-chars-long

# Optional
DATABASE_URL=postgresql://user:password@localhost:5432/shopbot
WEBHOOK_URL=https://yourdomain.com/webhook
REDIS_URL=redis://localhost:6379/0
```

### Telegram Bot Setup

1. Create a bot with [@BotFather](https://t.me/BotFather)
2. Get your bot token
3. Set webhook (optional):
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://yourdomain.com/webhook/telegram"}'
```

### NOWPayments Setup

1. Create account at [NOWPayments](https://nowpayments.io)
2. Get API key from dashboard
3. Configure IPN callback URL: `https://yourdomain.com/webhook/payment-ipn`
4. Set up supported cryptocurrencies

## 📱 Bot Commands

### User Commands
- `/start` - Start the bot and see welcome message
- `/menu` - Show main menu
- `/cart` - View shopping cart
- `/orders` - View order history
- `/support` - Contact customer support
- `/language` - Change language
- `/profile` - View user profile and stats

### Admin Commands (via bot)
- `/admin` - Access admin functions
- `/broadcast` - Send message to all users
- `/stats` - Get system statistics

## 🌐 Web Admin Panel

Access the admin panel at `http://localhost:8000`

### Main Features

#### Dashboard
- Sales overview and statistics
- Recent orders and activity
- System health monitoring
- Quick action buttons

#### Product Management
- Add/edit/delete products
- Category management
- Inventory tracking
- Bulk operations
- Image upload and management

#### Order Management
- Order processing workflow
- Status updates and tracking
- Customer communication
- Refund processing
- Shipping integration

#### User Management
- Customer profiles and history
- Admin user management
- Role assignments
- Activity monitoring
- Loyalty point management

#### Analytics
- Sales trends and forecasting
- Customer behavior analysis
- Product performance metrics
- Payment method analytics
- Geographic distribution

#### Marketing
- Discount code management
- Promotion campaigns
- Referral program settings
- Email marketing tools
- Customer segmentation

#### Support
- Ticket management system
- Live chat interface
- FAQ management
- Response templates
- Customer satisfaction tracking

#### Settings
- System configuration
- Payment gateway settings
- Notification preferences
- Backup management
- Security settings

## 🏗️ Architecture

### Project Structure
```
tg-shop-bot/
├── main.py                 # Application entry point
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── config/
│   └── settings.py        # Configuration management
├── database/
│   ├── __init__.py
│   ├── database.py        # Database connection
│   └── models.py          # SQLAlchemy models
├── bot/
│   ├── __init__.py
│   ├── bot.py            # Main bot logic
│   ├── keyboards.py      # Telegram keyboards
│   └── utils.py          # Bot utilities
├── web/
│   ├── __init__.py
│   ├── app.py            # FastAPI application
│   ├── auth.py           # Authentication system
│   ├── api.py            # API endpoints
│   ├── utils.py          # Web utilities
│   ├── static/           # Static files
│   └── templates/        # HTML templates
├── services/
│   ├── __init__.py
│   ├── nowpayments.py    # Payment processing
│   ├── qr_generator.py   # QR code generation
│   ├── analytics.py      # Analytics service
│   ├── backup.py         # Backup service
│   └── notifications.py # Notification service
└── translations/         # Language files
```

### Technology Stack

#### Backend
- **FastAPI** - Modern web framework for APIs
- **SQLAlchemy** - Database ORM
- **Alembic** - Database migrations
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage

#### Bot Framework
- **python-telegram-bot** - Telegram Bot API wrapper
- **asyncio** - Asynchronous programming

#### Payment Processing
- **NOWPayments API** - Cryptocurrency payments
- **QR Code Generation** - Payment invoices

#### Security
- **JWT** - Authentication tokens
- **bcrypt** - Password hashing
- **pyotp** - Two-factor authentication
- **Rate limiting** - Request throttling

#### Frontend
- **HTML/CSS/JavaScript** - Admin panel interface
- **Bootstrap** - UI framework
- **Chart.js** - Analytics charts

## 📊 Database Schema

### Core Models

#### Users
- Personal information and preferences
- Authentication credentials
- Loyalty points and referral data
- Security settings (2FA)

#### Products
- Product details and media
- Pricing and inventory
- Categories and classifications
- Digital/physical product settings

#### Orders
- Order processing workflow
- Item details and pricing
- Shipping and billing information
- Status tracking

#### Payments
- NOWPayments integration data
- Transaction details
- QR code information
- Payment status tracking

#### Support
- Ticket management
- Message threading
- Assignment and resolution
- Customer satisfaction

### Relationships
- Users → Orders (one-to-many)
- Orders → OrderItems (one-to-many)
- Products → OrderItems (one-to-many)
- Users → SupportTickets (one-to-many)
- Categories → Products (one-to-many)

## 🔐 Security Features

### Authentication
- **JWT Tokens** - Secure session management
- **Password Hashing** - bcrypt encryption
- **2FA Support** - TOTP-based authentication
- **Rate Limiting** - Brute force protection

### Data Protection
- **Encrypted Storage** - Sensitive data encryption
- **Secure Headers** - XSS and CSRF protection
- **Input Validation** - SQL injection prevention
- **Audit Logging** - Complete activity tracking

### Payment Security
- **IPN Verification** - Webhook signature validation
- **Payment Isolation** - Secure payment processing
- **Transaction Logging** - Complete payment audit trail

## 📈 Scaling Considerations

### Horizontal Scaling
- **Load Balancing** - Multiple application instances
- **Database Sharding** - Distribute data across servers
- **Redis Clustering** - Distributed caching
- **CDN Integration** - Static file delivery

### Performance Optimization
- **Database Indexing** - Optimized queries
- **Caching Strategy** - Redis for frequent data
- **Connection Pooling** - Efficient database connections
- **Background Tasks** - Async processing

### Monitoring
- **Health Checks** - System status monitoring
- **Performance Metrics** - Response time tracking
- **Error Tracking** - Automatic error reporting
- **Resource Usage** - Memory and CPU monitoring

## 🌍 Internationalization

### Supported Languages
- English (en)
- Lithuanian (lt)

### Adding New Languages

1. **Create translation file**
```python
# translations/es.py
TRANSLATIONS = {
    "welcome_message": "¡Bienvenido a nuestra tienda!",
    "browse_products": "Explorar productos",
    # ... more translations
}
```

2. **Update bot utilities**
```python
# bot/utils.py
TRANSLATIONS["es"] = es_translations
```

3. **Add language option**
```python
# bot/keyboards.py
languages = [
    ("🇺🇸 English", "en"),
    ("🇱🇹 Lietuvių", "lt"),
    ("🇪🇸 Español", "es"),  # Add new language
]
```

## 🚀 Deployment

### Docker Deployment

1. **Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py", "run"]
```

2. **Docker Compose**
```yaml
version: '3.8'
services:
  bot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/shopbot
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: shopbot
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    
volumes:
  postgres_data:
```

### Production Deployment

1. **Server Setup**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql redis-server nginx

# Create application user
sudo useradd -m -s /bin/bash shopbot
sudo su - shopbot
```

2. **Application Setup**
```bash
git clone https://github.com/your-repo/tg-shop-bot.git
cd tg-shop-bot
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Database Setup**
```bash
sudo -u postgres createdb shopbot
sudo -u postgres createuser shopbot
sudo -u postgres psql -c "ALTER USER shopbot PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE shopbot TO shopbot;"
```

4. **Systemd Service**
```ini
# /etc/systemd/system/shopbot.service
[Unit]
Description=Telegram Shop Bot
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=shopbot
WorkingDirectory=/home/shopbot/tg-shop-bot
Environment=PATH=/home/shopbot/tg-shop-bot/venv/bin
ExecStart=/home/shopbot/tg-shop-bot/venv/bin/python main.py run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

5. **Nginx Configuration**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /webhook/ {
        proxy_pass http://127.0.0.1:8000/webhook/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🛠️ Development

### Setting Up Development Environment

1. **Clone and install**
```bash
git clone https://github.com/your-repo/tg-shop-bot.git
cd tg-shop-bot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Development configuration**
```bash
cp .env.example .env
# Edit .env with development settings
python main.py setup-db
python main.py create-admin
```

3. **Run in development mode**
```bash
python main.py dev
```

### Contributing

1. **Fork the repository**
2. **Create feature branch**
```bash
git checkout -b feature/amazing-feature
```

3. **Make changes and test**
```bash
# Run tests
python -m pytest

# Check code style
black .
flake8 .
```

4. **Commit and push**
```bash
git add .
git commit -m "Add amazing feature"
git push origin feature/amazing-feature
```

5. **Create Pull Request**

### Code Style

- **Black** - Code formatting
- **Flake8** - Linting
- **Type hints** - Function annotations
- **Docstrings** - Function documentation

## 📋 API Documentation

### Authentication
All admin API endpoints require authentication via JWT token or API key.

### Endpoints

#### Products API
- `GET /api/products` - List products
- `POST /api/products` - Create product
- `GET /api/products/{id}` - Get product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

#### Orders API
- `GET /api/orders` - List orders
- `GET /api/orders/{id}` - Get order
- `PUT /api/orders/{id}/status` - Update order status
- `POST /api/orders/{id}/refund` - Process refund

#### Users API
- `GET /api/users` - List users
- `GET /api/users/{id}` - Get user
- `PUT /api/users/{id}` - Update user
- `POST /api/users/{id}/ban` - Ban user

#### Analytics API
- `GET /api/analytics/sales` - Sales data
- `GET /api/analytics/users` - User metrics
- `GET /api/analytics/products` - Product performance

## 🔧 Troubleshooting

### Common Issues

#### Bot Not Responding
1. Check bot token validity
2. Verify webhook configuration
3. Check network connectivity
4. Review bot logs

#### Payment Issues
1. Verify NOWPayments API key
2. Check IPN callback URL
3. Validate webhook signatures
4. Review payment logs

#### Database Errors
1. Check database connection
2. Verify credentials
3. Run migrations
4. Check disk space

#### Performance Issues
1. Monitor resource usage
2. Check database queries
3. Review cache hit rates
4. Optimize slow endpoints

### Logs and Monitoring

#### Log Files
- `logs/shopbot_YYYY-MM-DD.log` - Application logs
- System logs via journalctl (systemd)

#### Monitoring Endpoints
- `GET /health` - Health check
- `GET /metrics` - Performance metrics
- `GET /admin/system-info` - System information

## 📞 Support

### Documentation
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [NOWPayments API](https://documenter.getpostman.com/view/7907941/S1a32n38)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Community
- GitHub Issues - Bug reports and feature requests
- Discussions - General questions and ideas

### Commercial Support
For commercial support, custom development, or enterprise features, contact [your-email@domain.com](mailto:your-email@domain.com).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot framework
- [FastAPI](https://github.com/tiangolo/fastapi) - Modern web framework
- [NOWPayments](https://nowpayments.io) - Cryptocurrency payment processor
- [SQLAlchemy](https://sqlalchemy.org) - Database toolkit

---

**Made with ❤️ for the crypto community**

*Start selling with cryptocurrency today! 🚀*