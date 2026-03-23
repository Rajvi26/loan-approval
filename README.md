# Loan Approval Prediction System

## Description

This is a Flask-based web application that predicts loan approval eligibility using machine learning models. The system includes user authentication, a responsive web interface, and detailed prediction reports with rejection reasons and suggestions.

## Features

- **Machine Learning Prediction**: Uses Random Forest Classifier trained on synthetic loan data to predict approval likelihood
- **User Authentication**: Secure registration, login, and password reset functionality
- **Detailed Reports**: Provides comprehensive rejection reports with specific reasons and improvement suggestions
- **Web Interface**: Responsive frontend built with HTML, CSS, and JavaScript
- **RESTful APIs**: API endpoints for authentication and prediction
- **SQLite Database**: Local database for user management

## Technologies Used

- **Backend**: Flask (Python)
- **Machine Learning**: scikit-learn (Random Forest)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Data Processing**: Pandas, NumPy

## Installation

1. Clone the repository or download the project files.

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Register**: Create a new account using the signup page.
2. **Login**: Authenticate with your email and password.
3. **Predict Loan Approval**: Fill in the loan application form with details like age, income, loan amount, etc.
4. **View Results**: Get instant prediction results with detailed reports if rejected.

## Dataset

The project includes `logical_realistic_loan_dataset.csv` which contains realistic loan application data for analysis and testing.

## Jupyter Notebook

`FINALIST_LOAN_APPROVAL_PROJECT.ipynb` contains the data analysis, model training, and evaluation code.

## API Endpoints

### Authentication

- `POST /api/signup` - User registration
- `POST /api/login` - User login
- `POST /api/forgot-password` - Password reset
- `POST /api/logout` - User logout
- `GET /api/check-auth` - Check authentication status

### Prediction

- `POST /predict` - Submit loan application for prediction

## Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Considerations

- Passwords are securely hashed using Werkzeug
- Session-based authentication
- Input validation for email and passwords
- For production deployment, consider additional security measures like HTTPS, rate limiting, and email verification.

## Contributing

Feel free to contribute by submitting issues or pull requests.