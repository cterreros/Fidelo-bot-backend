# FideloBot Backend

This is the backend of the **FideloBot** project, a loyalty system for small businesses that allows registering purchases, assigning points to customers, and automating messages (e.g., birthday greetings via Telegram bot).

---

## 🚀 Technologies Used

- Python 3.11.5  
- Django 5.x  
- Django Rest Framework (DRF)  
- PostgreSQL  
- (Upcoming) python-telegram-bot, APScheduler or Celery  

---

## 🧱 Technical Objective

This project is structured to become:

- 🧩 A reusable loyalty library  
- ☁️ A hosted SaaS service (multi-business)  
- 🤖 A bot with simple channel integration (Telegram, WhatsApp)  

---

## 🔧 How to Start the Project (Step-by-Step)

### 1. Install Python 3.11.5 (if not installed)

Download Python from the official source:

👉 https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe

> ✅ During installation, make sure to check **"Add Python to PATH"**

Then verify installation:

```bash
python --version
```

You should see:

```
Python 3.11.5
```

---

### 2. Clone the repository

```bash
git clone https://github.com/tuusuario/fidelo-bot-backend.git
cd fidelo-bot-backend
```

---

### 3. Create and activate a virtual environment

```bash
python -m venv venv
```

Activate the virtual environment:

- On **Windows**:

```bash
.\env\Scripts\activate
```

- On **Linux/macOS**:

```bash
source venv/bin/activate
```

---

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Apply database migrations

```bash
python manage.py migrate
```

---

### 6. Run the development server (use port 8080)

```bash
python manage.py runserver 127.0.0.1:8080
```

Now visit in your browser:

http://127.0.0.1:8080
