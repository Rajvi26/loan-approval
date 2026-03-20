import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Loan AI", layout="wide")

# DEBUG LINE (remove later)
st.write("✅ LOAN1 FILE RUNNING")

st.title("🏦 AI Loan Approval System")

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
@st.cache_resource
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

model, scaler, columns = train_model()

# =========================
# INPUT UI (NO SLIDER)
# =========================
col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age", min_value=18, max_value=60, value=25)
    income = st.number_input("Monthly Income (₹)", min_value=10000, value=50000)
    credit_score = st.number_input("Credit Score", min_value=100, max_value=900, value=650)
    months_employed = st.number_input("Months Employed", min_value=0, value=24)
    num_credit_lines = st.number_input("Number of Credit Lines", min_value=0, value=2)

with col2:
    loan_amount = st.number_input("Loan Amount (₹)", min_value=10000, value=200000)
    loan_term = st.number_input("Loan Term (Months)", min_value=6, max_value=360, value=36)
    purpose = st.selectbox("Loan Purpose", ["Home", "Auto", "Other"])

# =========================
# PREDICTION
# =========================
if st.button("Predict Loan Status"):

    reasons = []

    # AGE RULE
    if age < 18 or age > 59:
        st.error("❌ Rejected: Age must be between 18–59")
        st.stop()

    # CREDIT RULE
    if age <= 27 and not (100 <= credit_score <= 450):
        st.error("❌ Rejected: Credit score rule failed (age 18–27)")
        st.stop()

    if age > 27 and not (500 <= credit_score <= 900):
        st.error("❌ Rejected: Credit score too low")
        st.stop()

    # AUTO INTEREST
    if purpose == "Home":
        interest = 8 if income > 50000 else 10
    elif purpose == "Auto":
        interest = 10
    else:
        interest = 12

    st.info(f"📊 Interest Rate Applied: {interest}%")

    # EMI CALCULATION
    emi = calculate_emi(loan_amount, interest, loan_term)
    emi_ratio = emi / income

    # EMI RULE
    if emi > 0.5 * income:
        st.error("❌ Rejected: EMI > 50% of income")
        st.stop()
    else:
        reasons.append("EMI within safe limit")

    st.info(f"📊 EMI: ₹{round(emi,2)}")
    st.info(f"📉 EMI Ratio: {round(emi_ratio,2)}")

    # ML INPUT
    input_data = pd.DataFrame([[age, income, loan_amount, credit_score,
                                months_employed, num_credit_lines,
                                interest, loan_term, emi_ratio,
                                emi, income/(emi+1)]],
                                columns=columns)

    input_scaled = scaler.transform(input_data)

    pred = model.predict(input_scaled)[0]
    prob = model.predict_proba(input_scaled)[0]

    st.write(f"🤖 Approval Probability: {round(prob[0]*100,2)}%")

    # FINAL OUTPUT
    if pred == 0:
        st.success("✅ Loan Approved")
        for r in reasons:
            st.write("✔️", r)
        st.write("✔️ ML model: Low Risk")
    else:
        st.error("❌ Loan Rejected")
        st.write("❌ ML model: High Risk")