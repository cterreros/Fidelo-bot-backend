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

👉 [https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe](https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe)

> ✅ During installation, make sure to check **"Add Python to PATH"**  
> This will allow you to use `python` directly in the terminal.

After installation, verify with:

python --version
---
## Clone the repository

- git clone https://github.com/tuusuario/fidelo-bot-backend.git
- cd fidelo-bot-backend

---

### Create and activate a virtual environment

python -m venv venv
Activate the environment:

On Windows:
.\venv\Scripts\activate

On Linux/macOS:
source venv/bin/activate

---

### Install required dependencies

pip install -r requirements.txt

## Apply database migrations

python manage.py migrate

## Run the development server on port 

python manage.py runserver 127.0.0.1:8080
