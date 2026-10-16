from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from schemas.schemas import (
    HeartRiskInput, FullPersonalizedRecommendationResponse, RecommendationResponse
)
from services.recommendation_service import (
    build_personalized_recommendations, generate_recommendations
)
from services.prediction_service import predict_heart_risk
from database.database import get_db
from database.models import HealthAssessment, User
from services.auth_handler import get_current_user, get_optional_current_user

router = APIRouter(tags=["recommendations"])

@router.get("/api/recommendations", response_model=FullPersonalizedRecommendationResponse)
@router.get("/recommendations", response_model=FullPersonalizedRecommendationResponse, include_in_schema=False)
@router.get("/recommendations/me", response_model=FullPersonalizedRecommendationResponse, include_in_schema=False)
def get_user_recommendations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Core Recommendation API (GET /api/recommendations):
    Retrieves the authenticated user's:
    - Latest health assessment (or profile)
    - Recent logged problems
    - Previous prescriptions & current medicines
    - Documented allergies
    Then executes the recommendation engine and medicine safety screening layer.
    """
    latest_assessment = (
        db.query(HealthAssessment)
        .filter(HealthAssessment.user_id == user.id)
        .order_by(HealthAssessment.created_at.desc())
        .first()
    )

    if not latest_assessment:
        # Check if user has profile data to formulate baseline preventive guidance
        profile = user.profile
        if profile and profile.age:
            patient_data = {
                "age": profile.age,
                "gender": profile.gender or "Unspecified",
                "smoker_status": profile.smoker_status or "No",
                "diabetes_history": profile.diabetes_history or "No",
                "heart_rate": 72.0,
                "systolic_blood_pressure": 120.0,
                "oxygen_saturation": 98.0,
                "chest_pain_severity": 0.0,
                "body_temperature": 36.8
            }
            # Run baseline ML prediction
            ml_pred = predict_heart_risk(HeartRiskInput(**patient_data))
            return build_personalized_recommendations(
                patient_data=patient_data,
                risk_level=ml_pred["risk_level"],
                confidence=ml_pred["confidence"],
                probabilities=ml_pred["probabilities"],
                user=user,
                db=db
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No health assessment records found for this user. Please complete a health risk analysis first."
            )

    patient_data = {
        "age": latest_assessment.age,
        "gender": latest_assessment.gender,
        "smoker_status": latest_assessment.smoker_status,
        "diabetes_history": latest_assessment.diabetes_history,
        "heart_rate": latest_assessment.heart_rate,
        "systolic_blood_pressure": latest_assessment.systolic_blood_pressure,
        "oxygen_saturation": latest_assessment.oxygen_saturation,
        "chest_pain_severity": latest_assessment.chest_pain_severity,
        "body_temperature": latest_assessment.body_temperature
    }

    # Re-evaluate class probabilities via ML model to ensure complete distribution
    try:
        ml_pred = predict_heart_risk(HeartRiskInput(**patient_data))
        probabilities = ml_pred["probabilities"]
        risk_level = ml_pred["risk_level"]
        confidence = ml_pred["confidence"]
    except Exception:
        risk_level = latest_assessment.predicted_risk
        confidence = latest_assessment.confidence
        probabilities = {latest_assessment.predicted_risk: latest_assessment.confidence}

    return build_personalized_recommendations(
        patient_data=patient_data,
        risk_level=risk_level,
        confidence=confidence,
        probabilities=probabilities,
        user=user,
        db=db
    )

@router.post("/api/recommendations", response_model=FullPersonalizedRecommendationResponse)
@router.post("/recommendations", response_model=FullPersonalizedRecommendationResponse, include_in_schema=False)
def generate_recommendations_from_input(
    patient: HeartRiskInput,
    risk_level: Optional[str] = Query(None, description="Optional risk tier override; if omitted, computed via ML"),
    db: Session = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Computes personalized recommendations for given health inputs.
    If authenticated, seamlessly incorporates the user's recent problems, prescriptions, and allergies.
    """
    patient_dict = patient.model_dump()

    # Execute ML model to obtain risk prediction and probabilities
    ml_result = predict_heart_risk(patient)
    actual_risk = risk_level or ml_result["risk_level"]
    confidence = ml_result["confidence"]
    probabilities = ml_result["probabilities"]

    return build_personalized_recommendations(
        patient_data=patient_dict,
        risk_level=actual_risk,
        confidence=confidence,
        probabilities=probabilities,
        user=optional_user,
        db=db
    )
