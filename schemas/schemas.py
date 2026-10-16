from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# ==================== Authentication & User Schemas ====================

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileOut(BaseModel):
    id: int
    user_id: int
    age: Optional[int] = None
    gender: Optional[str] = None
    smoker_status: Optional[str] = None
    diabetes_history: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    smoker_status: Optional[str] = None
    diabetes_history: Optional[str] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
    profile: Optional[UserProfileOut] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ==================== Health Risk & Prediction ====================

class HeartRiskInput(BaseModel):
    age: int = Field(..., ge=1, le=120, description="Age in years")
    gender: str = Field(..., description="Gender (Male/Female)")
    smoker_status: str = Field(..., description="Smoker status (Yes/No)")
    diabetes_history: str = Field(..., description="Diabetes history (Yes/No)")
    heart_rate: float = Field(..., ge=30, le=250, description="Heart rate (bpm)")
    systolic_blood_pressure: float = Field(..., ge=50, le=280, description="Systolic blood pressure (mmHg)")
    oxygen_saturation: float = Field(..., ge=50, le=100, description="Oxygen saturation (%)")
    chest_pain_severity: float = Field(..., ge=0, le=10, description="Chest pain severity (0-10)")
    body_temperature: float = Field(..., ge=30, le=45, description="Body temperature (°C)")

class PredictionOnlyResult(BaseModel):
    risk_level: str
    confidence: float
    probabilities: Dict[str, float]

class DoctorRecommendationOut(BaseModel):
    recommended_specialist: str
    urgency: str
    reason: str
    discussion_points: List[str] = []

class ScreenedMedicineInfoOut(BaseModel):
    medicine_name: str
    generic_name: Optional[str] = None
    category: Optional[str] = None
    common_uses: Optional[str] = None
    warnings: Optional[str] = None
    contraindications: Optional[str] = None
    prescription_required: bool = False
    safe_to_display: bool = True
    potential_conflict: bool = False
    warning: Optional[str] = None
    reason: Optional[str] = None
    requires_professional_review: bool = True
    verified_database_record: bool = True
    interaction_screening_note: Optional[str] = None

class PatientContextSummary(BaseModel):
    recent_problems_count: int = 0
    previous_prescriptions_count: int = 0
    active_allergies_count: int = 0
    recent_symptoms_considered: List[str] = []
    current_medicines_considered: List[str] = []
    historical_medicines_considered: List[str] = []

class FullPersonalizedRecommendationResponse(BaseModel):
    risk_level: str
    confidence: float
    probabilities: Dict[str, float]
    what_to_do: List[str]
    what_not_to_do: List[str]
    doctor_recommendation: DoctorRecommendationOut
    medicine_information: List[ScreenedMedicineInfoOut] = []
    safety_warnings: List[str] = []
    emergency_warning: Optional[str] = None
    patient_context_used: Optional[PatientContextSummary] = None
    disclaimer: str

class RecommendationResponse(BaseModel):
    risk_level: str
    what_to_do: List[str]
    what_not_to_do: List[str]
    what_to_avoid: List[str]
    doctor: str
    doctor_guidance: str
    emergency_warning: Optional[str] = None

class PredictionResponse(BaseModel):
    risk_level: str
    confidence: float
    probabilities: Dict[str, float]
    recommendation: Dict[str, Any]
    recommendations: Dict[str, Any]
    medications: List[str]
    prescription: List[str]
    # Present only when the prediction was saved for an authenticated user.
    assessment_id: Optional[int] = None
    assessed_at: Optional[datetime] = None

class AssessmentHistoryOut(BaseModel):
    id: int
    user_id: int
    age: int
    gender: str
    smoker_status: str
    diabetes_history: str
    heart_rate: float
    systolic_blood_pressure: float
    oxygen_saturation: float
    chest_pain_severity: float
    body_temperature: float
    predicted_risk: str
    confidence: float
    # None for records saved before the probability distribution was persisted.
    probabilities: Optional[Dict[str, float]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AssessmentSaveRequest(BaseModel):
    age: int
    gender: str
    smoker_status: str
    diabetes_history: str
    heart_rate: float
    systolic_blood_pressure: float
    oxygen_saturation: float
    chest_pain_severity: float
    body_temperature: float
    predicted_risk: str
    confidence: float
    probabilities: Optional[Dict[str, float]] = None

# ==================== Recent Problems ====================

class ProblemCreate(BaseModel):
    problem_text: str = Field(..., min_length=2)
    problem_category: Optional[str] = None
    severity: Optional[str] = "Moderate"
    duration: Optional[str] = None
    status: Optional[str] = "Active"
    notes: Optional[str] = None

class ProblemUpdate(BaseModel):
    problem_text: Optional[str] = None
    problem_category: Optional[str] = None
    severity: Optional[str] = None
    duration: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ProblemOut(BaseModel):
    id: int
    user_id: int
    problem_text: str
    problem_category: Optional[str] = None
    severity: Optional[str] = None
    duration: Optional[str] = None
    status: Optional[str] = "Active"
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ==================== Allergies ====================

class AllergyCreate(BaseModel):
    allergen: str = Field(..., min_length=2)
    reaction: Optional[str] = None
    severity: Optional[str] = "Moderate"
    verification_status: Optional[str] = "Self-Reported"

class AllergyUpdate(BaseModel):
    allergen: Optional[str] = None
    reaction: Optional[str] = None
    severity: Optional[str] = None
    verification_status: Optional[str] = None

class AllergyOut(BaseModel):
    id: int
    user_id: int
    allergen: str
    reaction: Optional[str] = None
    severity: Optional[str] = None
    verification_status: Optional[str] = "Self-Reported"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==================== Prescriptions ====================

class PrescriptionMedicineCreate(BaseModel):
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None

class PrescriptionMedicineUpdate(BaseModel):
    medicine_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None

class PrescriptionMedicineOut(BaseModel):
    id: int
    prescription_id: int
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None

    class Config:
        from_attributes = True

class PrescriptionCreate(BaseModel):
    title: Optional[str] = None
    main_health_problem: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    prescription_date: Optional[datetime] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    file_path: Optional[str] = None
    original_filename: Optional[str] = None
    extraction_status: Optional[str] = "Manual"
    medicines: List[PrescriptionMedicineCreate] = []

class PrescriptionUpdate(BaseModel):
    title: Optional[str] = None
    main_health_problem: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    prescription_date: Optional[datetime] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    extraction_status: Optional[str] = None

class PrescriptionOut(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    prescription_date: Optional[datetime] = None
    main_health_problem: Optional[str] = None
    diagnosis: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    notes: Optional[str] = None
    file_path: Optional[str] = None
    original_filename: Optional[str] = None
    extraction_status: Optional[str] = "Manual"
    created_at: datetime
    updated_at: Optional[datetime] = None
    medicines: List[PrescriptionMedicineOut] = []

    class Config:
        from_attributes = True

# ==================== Health Timeline ====================

class TimelineEventOut(BaseModel):
    id: str
    event_type: str  # 'ASSESSMENT', 'SYMPTOM', 'PRESCRIPTION', 'ALLERGY', 'BRIEFING'
    title: str
    description: str
    event_date: datetime
    badge: Optional[str] = None
    severity: Optional[str] = None
    metadata: Dict[str, Any] = {}
    source_id: int
    source_link: str

# ==================== Doctor-Visit Briefings & Secure Sharing ====================

class DoctorBriefingCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    visit_reason: str = Field(..., min_length=2)
    symptoms_summary: Optional[str] = None
    vitals_summary: Optional[str] = None
    allergies_summary: Optional[str] = None
    medicines_summary: Optional[str] = None
    questions_to_ask: Optional[str] = None
    notes: Optional[str] = None

class DoctorBriefingUpdate(BaseModel):
    title: Optional[str] = None
    visit_reason: Optional[str] = None
    symptoms_summary: Optional[str] = None
    vitals_summary: Optional[str] = None
    allergies_summary: Optional[str] = None
    medicines_summary: Optional[str] = None
    questions_to_ask: Optional[str] = None
    notes: Optional[str] = None

class SharedBriefingOut(BaseModel):
    id: int
    briefing_id: int
    share_token: str
    recipient_name: Optional[str] = None
    recipient_role: Optional[str] = "Physician"
    has_pin: bool = False
    expires_at: datetime
    is_revoked: bool
    view_count: int
    last_accessed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DoctorBriefingOut(BaseModel):
    id: int
    user_id: int
    title: str
    visit_reason: str
    symptoms_summary: Optional[str] = None
    vitals_summary: Optional[str] = None
    allergies_summary: Optional[str] = None
    medicines_summary: Optional[str] = None
    questions_to_ask: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    shares: List[SharedBriefingOut] = []

    class Config:
        from_attributes = True

class ShareBriefingCreate(BaseModel):
    recipient_name: Optional[str] = "Physician"
    recipient_role: Optional[str] = "Physician"
    access_pin: Optional[str] = None
    duration_hours: int = Field(default=72, ge=1, le=720)  # up to 30 days

class PublicSharedBriefingOut(BaseModel):
    share_token: str
    patient_name: str
    title: str
    visit_reason: str
    symptoms_summary: Optional[str] = None
    vitals_summary: Optional[str] = None
    allergies_summary: Optional[str] = None
    medicines_summary: Optional[str] = None
    questions_to_ask: Optional[str] = None
    notes: Optional[str] = None
    recipient_name: Optional[str] = None
    expires_at: datetime
    is_expired: bool
    created_at: datetime

# ==================== Medicines & Interactions ====================

class MedicineCreate(BaseModel):
    medicine_name: str
    generic_name: Optional[str] = None
    category: Optional[str] = None
    common_uses: Optional[str] = None
    contraindications: Optional[str] = None
    warnings: Optional[str] = None
    prescription_required: bool = False

class MedicineOut(BaseModel):
    id: int
    medicine_name: str
    generic_name: Optional[str] = None
    category: Optional[str] = None
    common_uses: Optional[str] = None
    contraindications: Optional[str] = None
    warnings: Optional[str] = None
    prescription_required: bool

    class Config:
        from_attributes = True

class MedicineInteractionCreate(BaseModel):
    medicine_a: str
    medicine_b: str
    interaction_level: str
    description: Optional[str] = None

class MedicineInteractionOut(BaseModel):
    id: int
    medicine_a: str
    medicine_b: str
    interaction_level: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class MedicineCheckRequest(BaseModel):
    medicine_name: str
    patient_conditions: Optional[List[str]] = None
    current_meds: Optional[List[str]] = None

class MedicineCheckResponse(BaseModel):
    medicine_name: str
    medicine_info: Optional[MedicineOut] = None
    safety_warnings: List[str] = []
    interactions: List[Dict[str, Any]] = []
    contraindications: List[str] = []
    allergy_warnings: List[str] = []
    professional_consultation_required: bool = False
