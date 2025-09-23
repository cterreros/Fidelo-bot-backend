# 🤖 FideloBot - Intelligent Loyalty System

**FideloBot** is a complete loyalty system for small businesses that combines a **modern web form** with an **intelligent Telegram bot** to automatically manage customers, points, and purchases.

---

## ✨ **Key Features**

### 🏪 **Multi-Business Support**
- Support for multiple independent businesses
- Business authentication in web template
- Customizable points and bonus configuration

### 👤 **Intelligent Customer Management**
- **Automatic detection**: Customers registered on web are automatically detected in the bot
- **Seamless linking**: Web template ↔ Telegram without duplicates
- **Data completion**: Automatically completes missing information

### 💎 **Robust Points System**
- Automatic accumulation per purchase
- Birthday bonuses
- Complete event history
- Balance per business and total

### 🤖 **Complete Telegram Bot**
- Step-by-step guided registration
- Commands: `/points`, `/history`, `/profile`, `/help`
- Interactive button navigation
- Automatic purchase notifications

### 🌐 **Modern Web Template**
- Professional glassmorphism design
- Automatic detection of new vs existing customers
- Confirmation modal with customer data
- Responsive and modern interface

---

## 🚀 **Installation and Setup**

### **Prerequisites**
- Python 3.11+
- PostgreSQL 12+
- Telegram Bot (Token)

### **1. Clone the repository**
```bash
git clone https://github.com/yourusername/fidelo-bot-backend.git
cd fidelo-bot-backend
```

### **2. Create virtual environment**
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### **3. Install dependencies**
```bash
pip install -r requirements.txt
```

### **4. Configure PostgreSQL Database**

**Create the database:**
```sql
-- In PostgreSQL
CREATE DATABASE fidelo_db;
CREATE USER fidelo_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE fidelo_db TO fidelo_user;
```

### **5. Configure Environment Variables**

Create `.env` file in project root:

```env
# Database
DB_NAME=fidelo_db
DB_USER=fidelo_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
DEBUG=True
SECRET_KEY=your-very-long-and-secure-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:AAE-YourBotToken

# Twilio SMS (Optional - Currently disabled)
# TWILIO_ACCOUNT_SID=your_account_sid
# TWILIO_AUTH_TOKEN=your_auth_token
# TWILIO_PHONE_NUMBER=+1234567890
# SMS_MODE=development
```

### **6. Apply migrations**
```bash
python manage.py migrate
```

### **7. Create superuser (optional)**
```bash
python manage.py createsuperuser
```

### **8. Create sample data**
```bash
python manage.py shell
```
```python
from core.models import Business

# Create sample businesses
Business.objects.create(
    name="Good Taste Coffee Shop",
    email="coffee@example.com",
    points_per_currency=0.1,
    birthday_bonus_points=100
)

Business.objects.create(
    name="Super Savings Store",
    email="store@example.com",
    points_per_currency=0.05,
    birthday_bonus_points=50
)
```

### **9. Start the server**
```bash
python manage.py runserver 127.0.0.1:8080
```

### **10. Configure Telegram Bot**

**In a separate terminal, run the bot:**
```bash
python manage.py shell
```
```python
from telegram_bot.bot import bot_instance
import asyncio

# Start the bot
app = bot_instance.get_application()
print("Bot starting...")
app.run_polling()
```

---

## 🎯 **System Usage**

### **📱 For Businesses (Web Template)**

1. **Access form**: `http://127.0.0.1:8080/purchase-form/`
2. **Select business** from dropdown
3. **Register purchase** with customer data:
   - New customers: Created automatically
   - Existing customers: Detected by phone
4. **Confirmation**: Modal shows points earned and total

### **🤖 For Customers (Telegram Bot)**

1. **Search** `@YourBotName` in Telegram
2. **Start** with `/start`
3. **Select business** where they made purchases
4. **Enter phone**: System automatically detects previous purchases
5. **Navigate** with buttons:
   - 🎯 View My Points
   - 📊 View Complete History
   - 🎁 Loyalty Programs

### **⚡ Bot Commands**

| Command | Description |
|---------|-------------|
| `/start` | Start/restart the bot |
| `/points` | View points balance |
| `/history` | View complete history |
| `/profile` | View profile information |
| `/help` | Commands list |
| `/link_telegram email` | Link existing account |

---

## 🔧 **API Endpoints**

### **Purchase Management**
```http
POST /api/purchases/
Content-Type: application/json

{
  "business_id": "uuid",
  "amount": "100.00",
  "currency": "MXN",
  "client_name": "John Doe",
  "client_email": "john@example.com",
  "client_phone": "+529511577561",
  "client_birthday": "1990-05-15",
  "send_telegram_notification": true
}
```

### **Query Points**
```http
GET /api/clients/?business_id=uuid&phone=+529511577561
```

### **View History**
```http
GET /api/point-events/?client_id=uuid
```

---

## 📊 **Project Structure**

```
fidelo-bot-backend/
├── core/                    # Main app
│   ├── models.py           # Models: Business, Client, Purchase, etc.
│   ├── views.py            # API views and template views
│   ├── serializers.py      # DRF serializers
│   ├── services.py         # Business logic
│   └── sms_service.py      # SMS service (disabled)
├── telegram_bot/           # Telegram bot
│   ├── bot.py              # Main bot
│   └── advanced_bot_features.py # Advanced features
├── templates/              # HTML templates
│   └── purchase_form.html  # Main form
├── static/                 # CSS, JS, images
├── fidelo_backend/         # Django configuration
│   └── settings.py
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables example
└── README.md              # This file
```

---

## 🧪 **Complete Test Flow**

### **Case 1: New Customer**
1. **Web**: Register purchase with phone `+529511577561`
2. **Bot**: `/start` → Select same business → Enter same phone
3. **Result**: ✅ "Phone found!" + shows points and history

### **Case 2: Existing Customer**
1. **Bot**: User already registered
2. **Web**: Register new purchase with same phone
3. **Bot**: `/points` → See automatically updated points

---

## 🔍 **Logs and Debugging**

**View bot logs:**
```bash
# Logs appear in the console where you run the bot
# Look for lines like:
DEBUG: Searching for phone '+529511577561' in business 'Coffee Shop'
DEBUG: FOUND client 'John Doe' with phone '+529511577561'
```

**View Django logs:**
```bash
# In the runserver terminal
# HTTP requests and errors appear
```

---

## 📈 **Upcoming Features**

- [ ] **Admin Dashboard** for businesses
- [ ] **Rewards System** (point redemption)
- [ ] **Automated Promotions & Coupons**
- [ ] **WhatsApp Business** API integration
- [ ] **Detailed Reports & Analytics**
- [ ] **Multi-language** (Spanish/English)
- [ ] **POS Systems** API

---

## 🤝 **Contributing**

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 **License**

This project is under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 💬 **Support**

Have questions or need help?

- 📧 Email: support@fidelo.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/fidelo-bot-backend/issues)
- 💬 Telegram: [@FideloBotSupport](https://t.me/FideloBotSupport)

---

## 🏆 **Credits**

Developed with ❤️ by the FideloBot team

**Tech Stack:**
- [Django](https://djangoproject.com/) - Web framework
- [Django REST Framework](https://django-rest-framework.org/) - REST API
- [PostgreSQL](https://postgresql.org/) - Database
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot
- [Font Awesome](https://fontawesome.com/) - Icons

---

<div align="center">

**⭐ If you like this project, give it a star on GitHub!**

[⬆ Back to top](#-fidelobot---intelligent-loyalty-system)

</div>