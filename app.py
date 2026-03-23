# ============================================================
# Loan Approval Prediction Application
# This Flask-based web application predicts loan approval
# using machine learning models (Random Forest Classifier)
# ============================================================

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import re

# Flask API
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a random secret key


# Database setup
DATABASE = 'users.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        db.commit()

# Initialize database
init_db()

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# =========================
# EMI FUNCTION
# =========================
def calculate_emi(P, rate, n):
    r = rate / (12 * 100)
    if r == 0:
        return P / n
    return (P * r * (1+r)**n) / ((1+r)**n - 1)

# =========================
# TRAIN MODEL
# =========================
def train_model():
    np.random.seed(42)

    df = pd.DataFrame({
        "Age": np.random.randint(22, 60, 2000),
        "EmploymentType": np.random.choice(["Salaried", "Business",  "Part time"], 2000),
        "Income": np.random.randint(20000, 150000, 2000),
        "LoanAmount": np.random.randint(10000, 500000, 2000),
        "CreditScore": np.random.randint(300, 850, 2000),
        "MonthsEmployed": np.random.randint(0, 200, 2000),
        "NumCreditLines": np.random.randint(1, 10, 2000),
        "InterestRate": np.random.uniform(7, 15, 2000),
        "LoanTerm": np.random.choice([12,24,36,60,120], 2000),
        "DTIRatio": np.random.uniform(0.1, 0.9, 2000),
        "Default": np.random.choice([0,1], 2000, p=[0.8,0.2])
    })

    # Encode categorical EmploymentType
    le = LabelEncoder()
    df["EmploymentType"] = le.fit_transform(df["EmploymentType"])

    df["EMI"] = df.apply(lambda x: calculate_emi(x["LoanAmount"], x["InterestRate"], x["LoanTerm"]), axis=1)
    df["Income_to_EMI"] = df["Income"] / (df["EMI"]+1)

    X = df.drop("Default", axis=1)
    y = df["Default"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = RandomForestClassifier()
    model.fit(X_scaled, y)

    return model, scaler, X.columns, le

# Train once at startup
print("🔄 Training model...")
model, scaler, columns, le = train_model()
print("✅ Model ready!")

# =========================
# AUTHENTICATION ROUTES
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template("login.html")
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['email'] = user['email']
            flash('Login successful!', 'success')
            return redirect(url_for('predict_page'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template("signup.html")
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template("signup.html")
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template("signup.html")
        
        hashed_password = generate_password_hash(password)
        
        db = get_db()
        try:
            db.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
            db.commit()
            # Get the user id
            user = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            session['user_id'] = user['id']
            session['email'] = email
            flash('Account created successfully!', 'success')
            return redirect(url_for('predict_page'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'error')
    
    return render_template("signup.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template("forgot_password.html")
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            # For simplicity, reset to a default password
            # In production, send email with reset link
            default_password = "reset123"
            hashed_password = generate_password_hash(default_password)
            db.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
            db.commit()
            flash(f'Password reset to: {default_password}. Please change it after login.', 'success')
        else:
            flash('Email not found', 'error')
    
    return render_template("forgot_password.html")

@app.route("/logout")
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route("/predict")
def predict_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("index.html")

# =========================
# API ROUTES
# =========================

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400
    
    hashed_password = generate_password_hash(password)
    
    db = get_db()
    try:
        db.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
        db.commit()
        return jsonify({"status": "success", "message": "Account created successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Email already exists"}), 400

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['email'] = user['email']
        return jsonify({"status": "success", "message": "Login successful", "user": {"email": user['email']}})
    else:
        return jsonify({"status": "error", "message": "Invalid email or password"}), 401

@app.route("/api/forgot-password", methods=["POST"])
def api_forgot_password():
    data = request.get_json()
    email = data.get("email")
    
    if not email:
        return jsonify({"status": "error", "message": "Email required"}), 400
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user:
        # For simplicity, reset to a default password
        default_password = "reset123"
        hashed_password = generate_password_hash(default_password)
        db.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
        db.commit()
        return jsonify({"status": "success", "message": f"Password reset to: {default_password}"})
    else:
        return jsonify({"status": "error", "message": "Email not found"}), 404

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logged out successfully"})

@app.route("/api/check-auth")
def check_auth():
    if 'user_id' in session:
        return jsonify({"authenticated": True, "user": {"email": session['email']}})
    else:
        return jsonify({"authenticated": False}), 401

# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('predict_page'))

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        age = int(data["age"])
        employment_type = data["employment_type"]
        income = int(data["income"])
        loan_amount = int(data["loan_amount"])
        credit_score = int(data["credit_score"])
        months_employed = int(data["months_employed"])
        num_credit_lines = int(data["num_credit_lines"])
        loan_term = int(data["loan_term"])
        purpose = data["purpose"]

        reasons = []

        # Helper: build rejection report
        def build_report(primary_reason, rejection_reasons, suggestions):
            return {
                "summary": primary_reason,
                "rejection_reasons": rejection_reasons,
                "applicant_snapshot": {
                    "Age": age,
                    "Employment Type": employment_type,
                    "Monthly Income": f"₹{income:,}",
                    "Loan Amount": f"₹{loan_amount:,}",
                    "Credit Score": credit_score,
                    "Months Employed": months_employed,
                    "Credit Lines": num_credit_lines,
                    "Loan Term": f"{loan_term} months",
                    "Purpose": purpose
                },
                "suggestions": suggestions
            }

        # AGE RULE
        if age < 18 or age > 59:
            report = build_report(
                "Your age does not meet our eligibility criteria.",
                [
                    {
                        "title": "Age Out of Range",
                        "description": f"Your age ({age}) is outside the eligible range of 18–59 years.",
                        "your_value": str(age),
                        "required": "18 – 59 years"
                    }
                ],
                [
                    "Applicants must be at least 18 years old to apply.",
                    "The maximum eligible age for a new loan is 59 years.",
                    "If you are close to the age limit, consider applying with a co-applicant who meets the criteria."
                ]
            )
            return jsonify({
                "status": "rejected",
                "reason": f"Age ({age}) must be between 18–59",
                "details": ["Age must be between 18–59 years"],
                "report": report
            })

        # CREDIT RULE (Young applicants)
        if age <= 27 and not (100 <= credit_score <= 450):
            report = build_report(
                "Your credit score does not meet the requirement for your age group.",
                [
                    {
                        "title": "Credit Score Mismatch (Age 18–27)",
                        "description": f"Applicants aged 18–27 must have a credit score between 100 and 450. Your score is {credit_score}.",
                        "your_value": str(credit_score),
                        "required": "100 – 450"
                    }
                ],
                [
                    "For the 18–27 age group, we use a different credit scoring scale (100–450).",
                    f"Your current credit score of {credit_score} {'exceeds' if credit_score > 450 else 'is below'} this range.",
                    "Ensure your credit report is up-to-date and consider correcting any discrepancies.",
                    "Building a stronger credit history through timely payments can improve your score."
                ]
            )
            return jsonify({
                "status": "rejected",
                "reason": f"Credit score rule failed (age 18–27 requires score 100–450)",
                "details": [f"Credit Score ({credit_score}) outside required range 100–450 for age group 18–27"],
                "report": report
            })

        # CREDIT RULE (Older applicants)
        if age > 27 and not (500 <= credit_score <= 900):
            report = build_report(
                "Your credit score is below the minimum requirement for your age group.",
                [
                    {
                        "title": "Credit Score Too Low (Age 28+)",
                        "description": f"Applicants aged 28 and above need a credit score between 500 and 900. Your score is {credit_score}.",
                        "your_value": str(credit_score),
                        "required": "500 – 900"
                    }
                ],
                [
                    f"Your credit score of {credit_score} is {'below the minimum of 500' if credit_score < 500 else 'above the maximum of 900'}.",
                    "Pay off outstanding debts and avoid late payments to gradually improve your score.",
                    "Review your credit report for errors that may be dragging your score down.",
                    "Maintain a low credit utilization ratio (below 30%) for a healthier score.",
                    "Consider waiting 3–6 months while building credit before re-applying."
                ]
            )
            return jsonify({
                "status": "rejected",
                "reason": f"Credit score too low (age 28+ requires score 500–900)",
                "details": [f"Credit Score ({credit_score}) outside required range 500–900 for age group 28+"],
                "report": report
            })

        # INTEREST RATE
        if purpose == "Home":
            interest = 8 if income > 50000 else 10
        elif purpose == "Auto":
            interest = 10
        else:
            interest = 12

        # EMI CALCULATION
        emi = calculate_emi(loan_amount, interest, loan_term)
        emi_ratio = emi / income
        max_allowed_emi = 0.5 * income

        # EMI RULE
        if emi > max_allowed_emi:
            report = build_report(
                "Your monthly EMI would exceed 50% of your income, which is too high.",
                [
                    {
                        "title": "EMI-to-Income Ratio Exceeded",
                        "description": f"Your estimated EMI of ₹{round(emi):,} is {round(emi_ratio * 100, 1)}% of your monthly income (₹{income:,}). Maximum allowed is 50%.",
                        "your_value": f"₹{round(emi):,} ({round(emi_ratio * 100, 1)}%)",
                        "required": f"≤ ₹{round(max_allowed_emi):,} (50% of income)"
                    }
                ],
                [
                    f"Your EMI of ₹{round(emi):,} exceeds the safe limit of ₹{round(max_allowed_emi):,} (50% of income).",
                    f"Consider reducing your loan amount from ₹{loan_amount:,} to a lower amount.",
                    f"Increasing the loan term beyond {loan_term} months will reduce the monthly EMI.",
                    "Alternatively, demonstrating a higher monthly income may help qualify.",
                    "You could also consider a smaller loan with a co-applicant."
                ]
            )
            return jsonify({
                "status": "rejected",
                "reason": "EMI exceeds 50% of monthly income",
                "details": [
                    f"Monthly EMI (₹{round(emi):,}) exceeds 50% of income (₹{income:,})",
                    f"EMI-to-Income ratio: {round(emi_ratio * 100, 1)}% (max allowed: 50%)"
                ],
                "report": report
            })
        else:
            reasons.append("EMI within safe limit")

        # ML INPUT
        employment_type_encoded = le.transform([employment_type])[0]
        input_data = pd.DataFrame([[age, employment_type_encoded, income, loan_amount, credit_score,
                                    months_employed, num_credit_lines,
                                    interest, loan_term, emi_ratio,
                                    emi, income/(emi+1)]],
                                    columns=columns)

        input_scaled = scaler.transform(input_data)

        pred = model.predict(input_scaled)[0]
        prob = model.predict_proba(input_scaled)[0]

        if pred == 0:
            reasons.append("ML model: Low Risk")
            return jsonify({
                "status": "approved",
                "probability": round(prob[0] * 100, 2),
                "emi": round(emi, 2),
                "interest_rate": interest,
                "emi_ratio": round(emi_ratio, 2),
                "details": reasons
            })
        else:
            # ML rejection - build comprehensive report
            risk_factors = []
            ml_suggestions = []

            # Analyse contributing factors
            if credit_score < 600:
                risk_factors.append({
                    "title": "Low Credit Score",
                    "description": f"Your credit score of {credit_score} is on the lower side, which increases perceived risk.",
                    "your_value": str(credit_score),
                    "required": "600+ recommended"
                })
                ml_suggestions.append("Improve your credit score by paying bills on time and reducing outstanding debt.")

            if emi_ratio > 0.35:
                risk_factors.append({
                    "title": "High EMI-to-Income Ratio",
                    "description": f"Your EMI would be {round(emi_ratio * 100, 1)}% of your income. A ratio above 35% signals financial strain.",
                    "your_value": f"{round(emi_ratio * 100, 1)}%",
                    "required": "Below 35% recommended"
                })
                ml_suggestions.append("Reduce the loan amount or increase the loan term to lower the EMI burden.")

            if months_employed < 12:
                risk_factors.append({
                    "title": "Limited Employment History",
                    "description": f"You have only {months_employed} months of employment. Lenders prefer stable, longer employment.",
                    "your_value": f"{months_employed} months",
                    "required": "12+ months recommended"
                })
                ml_suggestions.append("A longer employment history demonstrates income stability. Consider re-applying after gaining more experience.")

            if loan_amount > income * 10:
                risk_factors.append({
                    "title": "High Loan-to-Income Multiple",
                    "description": f"The requested loan (₹{loan_amount:,}) is {round(loan_amount/income, 1)}x your monthly income. This is considered high risk.",
                    "your_value": f"{round(loan_amount/income, 1)}x income",
                    "required": "Below 10x recommended"
                })
                ml_suggestions.append("Request a lower loan amount relative to your income for better approval odds.")

            if num_credit_lines >= 6:
                risk_factors.append({
                    "title": "Too Many Credit Lines",
                    "description": f"Having {num_credit_lines} active credit lines suggests over-leverage.",
                    "your_value": str(num_credit_lines),
                    "required": "Below 6 recommended"
                })
                ml_suggestions.append("Close unused credit lines to reduce your overall debt exposure.")

            # If no specific factor was identified, add a general one
            if not risk_factors:
                risk_factors.append({
                    "title": "Overall Risk Profile",
                    "description": "Our AI model assessed your combined financial profile as high risk based on multiple factors.",
                    "your_value": "High Risk",
                    "required": "Low Risk"
                })
                ml_suggestions.append("Consider applying with a co-applicant or guarantor to strengthen your application.")
                ml_suggestions.append("Reduce the loan amount or choose a longer repayment term.")

            ml_suggestions.append("You may re-apply after improving the factors highlighted above.")

            report = build_report(
                "Our AI model has identified your application as high risk based on your financial profile.",
                risk_factors,
                ml_suggestions
            )

            return jsonify({
                "status": "rejected",
                "reason": "AI Model Assessment: High Risk Profile",
                "probability": round(prob[0] * 100, 2),
                "details": [f"ML Risk Probability: {round(prob[1] * 100, 2)}%"],
                "report": report
            })

    except Exception as e:
        return jsonify({"status": "error", "reason": str(e)}), 400


if __name__ == "__main__":
    app.run()
