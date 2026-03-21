# Loan-Prediction-using-Machine-Learning

## Features

- AI-powered loan approval prediction using Machine Learning (Random Forest Classifier)
- User authentication system with registration, login, and password reset
- SQLite database for user data storage
- RESTful APIs for authentication
- Responsive web interface

## User Authentication

### Web Pages
- **Login**: `/login` - User login form
- **Signup**: `/signup` - User registration form  
- **Forgot Password**: `/forgot-password` - Password reset form
- **Logout**: `/logout` - User logout

### API Endpoints

#### POST /api/signup
Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Account created successfully"
}
```

#### POST /api/login
Authenticate a user.

**Request Body:**
```json
{
  "email": "user@example.com", 
  "password": "password123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "user": {
    "email": "user@example.com"
  }
}
```

#### POST /api/forgot-password
Reset user password (resets to default password).

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "status": "success", 
  "message": "Password reset to: reset123"
}
```

#### GET /api/check-auth
Check if user is authenticated.

**Response (authenticated):**
```json
{
  "authenticated": true,
  "user": {
    "email": "user@example.com"
  }
}
```

**Response (not authenticated):**
```json
{
  "authenticated": false
}
```

#### POST /api/logout
Logout user.

**Response:**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open http://localhost:5000 in your browser

## Database

User data is stored in `users.db` SQLite database with the following schema:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Notes

- Passwords are hashed using Werkzeug security
- Session-based authentication
- For production use, consider:
  - Email verification for signup
  - Proper email-based password reset
  - Rate limiting
  - HTTPS
  - Password strength requirements