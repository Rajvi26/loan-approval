from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)

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

    df["EMI"] = df.apply(lambda x: calculate_emi(x["LoanAmount"], x["InterestRate"], x["LoanTerm"]), axis=1)
    df["Income_to_EMI"] = df["Income"] / (df["EMI"]+1)

    X = df.drop("Default", axis=1)
    y = df["Default"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = RandomForestClassifier()
    model.fit(X_scaled, y)

    return model, scaler, X.columns

# Train once at startup
print("🔄 Training model...")
model, scaler, columns = train_model()
print("✅ Model ready!")

# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        age = int(data["age"])
        income = int(data["income"])
        loan_amount = int(data["loan_amount"])
        credit_score = int(data["credit_score"])
        months_employed = int(data["months_employed"])
        num_credit_lines = int(data["num_credit_lines"])
        loan_term = int(data["loan_term"])
        purpose = data["purpose"]

        reasons = []

        # AGE RULE
        if age < 18 or age > 59:
            return jsonify({
                "status": "rejected",
                "reason": "Age must be between 18–59",
                "details": []
            })

        # CREDIT RULE
        if age <= 27 and not (100 <= credit_score <= 450):
            return jsonify({
                "status": "rejected",
                "reason": "Credit score rule failed (age 18–27 requires score 100–450)",
                "details": []
            })

        if age > 27 and not (500 <= credit_score <= 900):
            return jsonify({
                "status": "rejected",
                "reason": "Credit score too low (age 28+ requires score 500–900)",
                "details": []
            })

        # AUTO INTEREST
        if purpose == "Home":
            interest = 8 if income > 50000 else 10
        elif purpose == "Auto":
            interest = 10
        else:
            interest = 12

        # EMI CALCULATION
        emi = calculate_emi(loan_amount, interest, loan_term)
        emi_ratio = emi / income

        # EMI RULE
        if emi > 0.5 * income:
            return jsonify({
                "status": "rejected",
                "reason": "EMI exceeds 50% of monthly income",
                "details": []
            })
        else:
            reasons.append("EMI within safe limit")

        # ML INPUT
        input_data = pd.DataFrame([[age, income, loan_amount, credit_score,
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
            return jsonify({
                "status": "rejected",
                "reason": "ML model: High Risk",
                "probability": round(prob[0] * 100, 2),
                "details": ["ML model: High Risk"]
            })

    except Exception as e:
        return jsonify({"status": "error", "reason": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
