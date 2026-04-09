# KalviConnect Backend

This repository contains the backend service for the **KalviConnect** Academy Management System. It primarily handles a robust, password-less Authentication system using One-Time Passwords (OTP) and JSON Web Tokens (JWT).

## 🧱 Tech Stack
- **Framework**: Python 3, Django 4+
- **API Framework**: Django REST Framework (DRF)
- **Authentication**: JWT (`djangorestframework-simplejwt`)
- **Database**: SQLite (Development) / PostgreSQL (Production ready)
- **Configuration**: `python-decouple`

---

## ✨ Features
1. **Custom User Model**: Uses UUIDs for Primary Keys. The default username field is replaced with `phone` (+91 format constraint). Accounts default to the `parent` role.
2. **OTP Login**: Strictly OTP-based entry. Passwords are set as unusable.
3. **Advanced Security**:
   - OTP validation drops if expired (after 5 minutes).
   - Rate limiting applied aggressively (max 3 OTP requests / 10 mins per phone number).
   - OTPs are hashed on generation via Django's internal cryptographic hashers before being saved to the database.

---

## 🛠️ Setup & Installation

**1. Clone the repository / Navigate to the folder**
```bash
cd "d:\Project\Tution App MAD\Backend"
```

**2. Create & Activate Virtual Environment**
```powershell
python -m venv venv

# On Windows PowerShell
.\venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
# (If requirements.txt is absent, manually run mapping: pip install django djangorestframework djangorestframework-simplejwt python-decouple django-filter psycopg2-binary Pillow)
```

**4. Set up Environment Variables**
Ensure you have a `.env` file at the root containing your settings, for example:
```env
SECRET_KEY=django-insecure-your-secret-key
DEBUG=True
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

**5. Database Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

**6. Start the Server**
```bash
python manage.py runserver
```

---

## 📡 API Reference

All requests must have the header `Content-Type: application/json`.

### 1. Send OTP
Generates a 6-digit OTP and initiates delivery.

- **URL:** `/api/auth/send-otp`
- **Method:** `POST`
- **Body:**
  ```json
  {
      "phone": "+919876543210"
  }
  ```
- **Note during Development:** The OTP will be printed out in your server console inside a block looking like `MOCK SMS SERVICE`. 

### 2. Verify OTP
Validates the SMS code. If the user is new, it generates their account automatically. It grants Access and Refresh JWT Tokens.

- **URL:** `/api/auth/verify-otp`
- **Method:** `POST`
- **Body:**
  ```json
  {
      "phone": "+919876543210",
      "otp": "123456"
  }
  ```
- **Response:**
  ```json
  {
      "access": "eyJhbGciOi...",
      "refresh": "eyJhbGciOi...",
      "user": {
          "id": "uuid-string",
          "phone": "+919876543210",
          "role": "parent",
          "name": null,
          "is_active": true,
          "created_at": "timestamp"
      }
  }
  ```

### 3. Logout (Token Blacklist)
Invalidates an active session refresh token. Needs `Authorization: Bearer <access_token>` in headers.

- **URL:** `/api/auth/logout`
- **Method:** `POST`
- **Body:**
  ```json
  {
      "refresh": "eyJhbGciOi..."
  }
  ```

---

## 🧪 Testing

To run the automated test suites mapping rate limiting, validation, and auth flows:

```bash
python manage.py test accounts
```
