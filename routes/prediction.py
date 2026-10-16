import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from schemas.schemas import (
    HeartRiskInput, PredictionResponse, AssessmentHistoryOut, AssessmentSaveRequest
)
from services.prediction_service import predict_heart_risk
from services.recommendation_service import (
    generate_recommendations, generate_medications_guidance
)
from database.database import get_db
from database.models import HealthAssessment, User
from services.auth_handler import get_current_user, get_optional_current_user

router = APIRouter(prefix="/predict", tags=["prediction"])

@router.post("", response_model=PredictionResponse, include_in_schema=False)
@router.post("/", response_model=PredictionResponse)
def run_prediction(
    data: HeartRiskInput,
    db: Session = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Core prediction endpoint.
    1. ML Model predicts risk category, confidence, and class probabilities.
    2. Decoupled Recommendation Engine generates clinical lifestyle guidance and medication information.
    3. If the user is authenticated, automatically persists the assessment to `health_assessments`.
    """
    try:
        # ML model prediction ONLY
        ml_result = predict_heart_risk(data)

        # Recommendation and safety guidance layer
        patient_dict = data.model_dump()
        rec_data = generate_recommendations(patient_dict, ml_result["risk_level"])
        meds_data = generate_medications_guidance(patient_dict, ml_result["risk_level"])

        # Auto-save to health_assessments if user is authenticated
        assessment_id = None
        assessed_at = None
        if optional_user:
            try:
                assessment = HealthAssessment(
                    user_id=optional_user.id,
                    age=data.age,
                    gender=data.gender,
                    smoker_status=data.smoker_status,
                    diabetes_history=data.diabetes_history,
                    heart_rate=data.heart_rate,
                    systolic_blood_pressure=data.systolic_blood_pressure,
                    oxygen_saturation=data.oxygen_saturation,
                    chest_pain_severity=data.chest_pain_severity,
                    body_temperature=data.body_temperature,
                    predicted_risk=ml_result["risk_level"],
                    confidence=ml_result["confidence"],
                    probabilities_json=json.dumps(ml_result["probabilities"])
                )
                db.add(assessment)
                db.commit()
                db.refresh(assessment)
                assessment_id = assessment.id
                assessed_at = assessment.created_at
            except Exception as save_err:
                db.rollback()
                print(f"[Prediction] Warning: auto-save assessment failed: {save_err}")

        return {
            "risk_level": ml_result["risk_level"],
            "confidence": ml_result["confidence"],
            "probabilities": ml_result["probabilities"],
            "recommendation": rec_data,
            "recommendations": rec_data,
            "medications": meds_data,
            "prescription": meds_data,
            "assessment_id": assessment_id,
            "assessed_at": assessed_at
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Prediction error: {str(e)}")

@router.post("/save", status_code=status.HTTP_201_CREATED)
def save_assessment(
    assessment_in: AssessmentSaveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Saves a health assessment record to database for the authenticated user."""
    new_assessment = HealthAssessment(
        user_id=user.id,
        age=assessment_in.age,
        gender=assessment_in.gender,
        smoker_status=assessment_in.smoker_status,
        diabetes_history=assessment_in.diabetes_history,
        heart_rate=assessment_in.heart_rate,
        systolic_blood_pressure=assessment_in.systolic_blood_pressure,
        oxygen_saturation=assessment_in.oxygen_saturation,
        chest_pain_severity=assessment_in.chest_pain_severity,
        body_temperature=assessment_in.body_temperature,
        predicted_risk=assessment_in.predicted_risk,
        confidence=assessment_in.confidence,
        probabilities_json=json.dumps(assessment_in.probabilities) if assessment_in.probabilities else None
    )
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)
    return {
        "message": "Health assessment saved successfully.",
        "assessment_id": new_assessment.id
    }

@router.get("/history", response_model=List[AssessmentHistoryOut])
def get_user_assessment_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Retrieves all historical health assessments for the authenticated user only."""
    assessments = (
        db.query(HealthAssessment)
        .filter(HealthAssessment.user_id == user.id)
        .order_by(HealthAssessment.created_at.desc())
        .all()
    )
    return assessments

@router.get("/history/{assessment_id}", response_model=AssessmentHistoryOut)
def get_user_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Retrieves one stored assessment, only if it belongs to the authenticated user."""
    assessment = db.query(HealthAssessment).filter(
        HealthAssessment.id == assessment_id,
        HealthAssessment.user_id == user.id
    ).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment record not found or access denied."
        )
    return assessment

@router.delete("/history/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Deletes an assessment record belonging to the authenticated user."""
    assessment = db.query(HealthAssessment).filter(
        HealthAssessment.id == assessment_id,
        HealthAssessment.user_id == user.id
    ).first()

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment record not found or access denied."
        )

    db.delete(assessment)
    db.commit()
    return None
