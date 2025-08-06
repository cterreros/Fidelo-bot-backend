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
.\venv\Scripts\activate
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

### 5. Configure PostgreSQL database connection

#### 1. Create the database

Use **pgAdmin 4**:

- Open pgAdmin and connect to your local server
- Right-click `Databases` → `Create` → `Database...`
- Name it: `fidelo_db`  
- Make sure the owner is: `postgres`

#### 2. Create a `.env` file

At the root of the project, add a file named `.env`:

```env
DB_NAME=fidelo_db
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD
DB_HOST=localhost
DB_PORT=5432
```

> 🔒 Replace `YOUR_PASSWORD` with your actual PostgreSQL password.

#### 3. Confirm the following packages are installed:

```bash
pip install python-decouple psycopg2-binary
```

#### 4. In `fidelo/settings.py` replace `DATABASES` section:

```python
from decouple import config

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}
```

---

### 6. Apply migrations

```bash
python manage.py migrate
```

---

### 7. Run the development server (port 8080)

```bash
python manage.py runserver 127.0.0.1:8080
```

Visit: [http://127.0.0.1:8080](http://127.0.0.1:8080)

---

## 📁 Dev Files & Docs

- 🔗 Entity-Relationship Diagram: [`docs/fidelo_diagrama.drawio`](docs/fidelo_diagrama.drawio)
- 📝 Setup Guide: [`setup_backend.md`](setup_backend.md)

---
