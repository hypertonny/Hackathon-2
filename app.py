# ============================================================
# Streamlit UI for PEP Grade Prediction
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

sns.set(style="whitegrid")

# ============================================================
# Load Dataset
# ============================================================

@st.cache_data
def load_data():
    df = pd.read_excel("PEP_Student_Performance_Final.xlsx")

    # Drop unwanted columns
    if "Student_ID" in df.columns:
        df = df.drop(columns=["Student_ID"])

    # Derived features
    df["Fitness_Score"] = (df["Pushups"] + df["Situps"] + df["Beep_Test"]) / 3
    df["Speed_Index"] = 30 - df["Run_3km_Min"]
    df["Performance_Index"] = (df["Fitness_Score"] + df["Speed_Index"]) / 2

    # Final feature list
    x = [
        "Age", "Gender", "Height_cm", "Weight_kg", "BMI",
        "Run_3km_Min", "Pushups", "Situps", "Beep_Test",
        "Attendance_%", "Fitness_Score", "Speed_Index", "Performance_Index"
    ]

    X = df[x]
    y = df["Grade"]

    return df, X, y, x

df, X, y, feature_cols = load_data()

# ============================================================
# Encode target & build preprocessing + model pipeline
# ============================================================

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()

preprocess = ColumnTransformer([
    ('num', StandardScaler(), num_cols),
    ('cat', OneHotEncoder(drop='first'), cat_cols)
])

model = Pipeline(steps=[
    ('preprocess', preprocess),
    ('clf', LogisticRegression(max_iter=1000))
])

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.25, random_state=42)

# Train model
model.fit(X_train, y_train)

# ============================================================
# STREAMLIT UI
# ============================================================

st.title("🏋️ PEP Examination Grade Predictor")
st.markdown("""
This application predicts the **PEP Grade (A–F)** of a student based on 
their physical performance and attendance.

### ⚠️ Disclaimer  
You **must have at least 80% attendance** to qualify for A–D Grades.  
Otherwise, you will receive **F**.
""")

st.sidebar.header("Enter Student Details")

# ---------------- User Input UI ----------------
def user_input():
    Age = st.sidebar.slider("Age", 18, 30, 21)
    Gender = st.sidebar.selectbox("Gender", ["M", "F"])
    Height_cm = st.sidebar.slider("Height (cm)", 150, 200, 170)
    Weight_kg = st.sidebar.slider("Weight (kg)", 40, 120, 70)

    BMI = round(Weight_kg / (Height_cm/100)**2, 1)

    Run_3km_Min = st.sidebar.slider("3 km Run Time (min)", 10, 40, 20)
    Pushups = st.sidebar.slider("Pushups", 0, 35, 20)
    Situps = st.sidebar.slider("Situps", 0, 35, 20)
    Beep_Test = st.sidebar.slider("Beep Test Score", 1.0, 12.0, 6.0)

    Attendance = st.sidebar.slider("Attendance %", 50.0, 100.0, 85.0)

    Fitness_Score = (Pushups + Situps + Beep_Test) / 3
    Speed_Index = 30 - Run_3km_Min
    Performance_Index = (Fitness_Score + Speed_Index) / 2

    data = {
        "Age": Age,
        "Gender": Gender,
        "Height_cm": Height_cm,
        "Weight_kg": Weight_kg,
        "BMI": BMI,
        "Run_3km_Min": Run_3km_Min,
        "Pushups": Pushups,
        "Situps": Situps,
        "Beep_Test": Beep_Test,
        "Attendance_%": Attendance,
        "Fitness_Score": Fitness_Score,
        "Speed_Index": Speed_Index,
        "Performance_Index": Performance_Index,
    }

    return pd.DataFrame([data])

input_df = user_input()

st.subheader("📌 Input Data Preview")
st.write(input_df)

# ============================================================
# PREDICTION
# ============================================================

if st.button("Predict Grade"):
    attendance = input_df["Attendance_%"].values[0]
    if attendance < 80:
        pred_grade = "F"
        st.success(f"🎓 **Predicted Grade: {pred_grade}**")
        st.warning("⚠️ Attendance below 80% → Final Grade = **F**")
    else:
        pred_encoded = model.predict(input_df)[0]
        pred_grade = label_encoder.inverse_transform([pred_encoded])[0]
        st.success(f"🎓 **Predicted Grade: {pred_grade}**")

# ============================================================
# MODEL METRICS
# ============================================================

st.header("📊 Model Performance")

# --- Accuracy ---
y_pred_test = model.predict(X_test)
acc = accuracy_score(y_test, y_pred_test)
st.write(f"**Model Accuracy:** {acc:.3f}")

# --- Confusion Matrix ---
st.subheader("Confusion Matrix")

fig, ax = plt.subplots(figsize=(6,4))
cm = confusion_matrix(label_encoder.inverse_transform(y_test),
                      label_encoder.inverse_transform(y_pred_test),
                      labels=label_encoder.classes_)

sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=label_encoder.classes_,
            yticklabels=label_encoder.classes_,
            ax=ax)
st.pyplot(fig)

# --- Classification Report ---
st.subheader("Classification Report")
st.text(classification_report(
    label_encoder.inverse_transform(y_test),
    label_encoder.inverse_transform(y_pred_test)
))