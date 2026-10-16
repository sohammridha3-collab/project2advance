import os
from pathlib import Path
from typing import Dict, Any, Optional
import joblib
import numpy as np
import pandas as pd

from schemas.schemas import HeartRiskInput

# Global model reference loaded ONCE at application startup
_model = None

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "heart_risk_model.pkl"

def load_model(model_path: Optional[Path] = None) -> Any:
    """Loads heart_risk_model.pkl into memory once at application startup."""
    global _model
    path = model_path or DEFAULT_MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(f"Model file not found at {path}")

    try:
        _model = joblib.load(path)
        print(f"[ML Engine] Heart risk model loaded successfully from {path}")
        return _model
    except Exception as e:
        print(f"[ML Engine] ERROR loading model from {path}: {e}")
        raise e

def get_model() -> Any:
    """Returns the loaded model instance or loads it if not already initialized."""
    global _model
    if _model is None:
        return load_model()
    return _model

def prepare_model_features(data: HeartRiskInput) -> pd.DataFrame:
    """
    Transforms raw input into the exact feature format expected by heart_risk_model.pkl:
    ['age', 'gender', 'smoker_status', 'diabetes_history', 'heart_rate',
     'systolic_blood_pressure', 'oxygen_saturation', 'chest_pain_severity',
     'body_temperature', 'age_group', 'heart_rate_flag', 'oxygen_flag']
    """
    patient_dict = data.model_dump()
    patient_df = pd.DataFrame([patient_dict])

    # Categorical normalization matching the model's pipeline encoder
    gender_raw = str(patient_dict.get("gender", "")).strip().title()
    patient_df["gender"] = "Female" if gender_raw.startswith("F") else "Male"

    smoker_raw = str(patient_dict.get("smoker_status", "")).strip().lower()
    patient_df["smoker_status"] = "Yes" if smoker_raw in ["yes", "y", "true", "1"] else "No"

    diabetes_raw = str(patient_dict.get("diabetes_history", "")).strip().lower()
    patient_df["diabetes_history"] = "Yes" if diabetes_raw in ["yes", "y", "true", "1"] else "No"

    # Feature engineering bins matching pipeline training specification
    patient_df["age_group"] = pd.cut(
        patient_df["age"],
        bins=[-np.inf, 30, 45, 60, 75, np.inf],
        labels=["Young", "Adult", "Middle_Aged", "Senior", "Elderly"]
    )

    patient_df["heart_rate_flag"] = pd.cut(
        patient_df["heart_rate"],
        bins=[-np.inf, 60, 100, np.inf],
        labels=["Low", "Normal", "High"]
    )

    patient_df["oxygen_flag"] = pd.cut(
        patient_df["oxygen_saturation"],
        bins=[-np.inf, 94, 98, np.inf],
        labels=["Low", "Normal", "High"]
    )

    expected_features = [
        'age', 'gender', 'smoker_status', 'diabetes_history', 'heart_rate',
        'systolic_blood_pressure', 'oxygen_saturation', 'chest_pain_severity',
        'body_temperature', 'age_group', 'heart_rate_flag', 'oxygen_flag'
    ]

    return patient_df[expected_features]

def predict_heart_risk(data: HeartRiskInput) -> Dict[str, Any]:
    """
    ML model inference ONLY.
    Predicts health-risk category, confidence, and class probabilities.
    Does NOT prescribe medications or handle user data.
    """
    model = get_model()
    if model is None:
        raise RuntimeError("ML Model is not loaded.")

    input_df = prepare_model_features(data)

    prediction = model.predict(input_df)[0]
    probabilities = model.predict_proba(input_df)[0]

    if hasattr(model, "classes_"):
        classes = model.classes_
    elif hasattr(model, "named_steps") and hasattr(model.named_steps.get("model"), "classes_"):
        classes = model.named_steps["model"].classes_
    else:
        classes = [str(i) for i in range(len(probabilities))]

    confidence = float(np.max(probabilities))
    prob_dict = {str(cls): round(float(prob) * 100, 2) for cls, prob in zip(classes, probabilities)}

    return {
        "risk_level": str(prediction),
        "confidence": round(confidence * 100, 2),
        "probabilities": prob_dict
    }
