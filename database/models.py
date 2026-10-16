from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    profile = relationship("HealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    assessments = relationship("HealthAssessment", back_populates="user", cascade="all, delete-orphan")
    problems = relationship("RecentProblem", back_populates="user", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="user", cascade="all, delete-orphan")
    allergies = relationship("Allergy", back_populates="user", cascade="all, delete-orphan")
    briefings = relationship("DoctorBriefing", back_populates="user", cascade="all, delete-orphan")


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    smoker_status = Column(String(50), nullable=True)
    diabetes_history = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")


class HealthAssessment(Base):
    __tablename__ = "health_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=False)
    smoker_status = Column(String(50), nullable=False)
    diabetes_history = Column(String(50), nullable=False)
    heart_rate = Column(Float, nullable=False)
    systolic_blood_pressure = Column(Float, nullable=False)
    oxygen_saturation = Column(Float, nullable=False)
    chest_pain_severity = Column(Float, nullable=False)
    body_temperature = Column(Float, nullable=False)
    predicted_risk = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    # JSON-encoded class-probability output of the model at prediction time.
    # Nullable: assessments saved before this column existed have no stored distribution.
    probabilities_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    user = relationship("User", back_populates="assessments")

    @property
    def probabilities(self):
        """Decoded probability dict, or None when it was not stored."""
        if not self.probabilities_json:
            return None
        try:
            import json
            data = json.loads(self.probabilities_json)
            return {str(k): float(v) for k, v in data.items()}
        except (ValueError, TypeError, AttributeError):
            return None


class RecentProblem(Base):
    __tablename__ = "recent_problems"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_text = Column(Text, nullable=False)
    problem_category = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)
    duration = Column(String(100), nullable=True)
    status = Column(String(50), default="Active", nullable=False)  # 'Active', 'Resolved', 'Investigating'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    user = relationship("User", back_populates="problems")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=True)
    doctor_name = Column(String(100), nullable=True)
    hospital_name = Column(String(150), nullable=True)
    prescription_date = Column(DateTime(timezone=True), nullable=True)
    main_health_problem = Column(String(200), nullable=True)
    diagnosis = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=True)
    original_filename = Column(String(255), nullable=True)
    extraction_status = Column(String(50), default="Manual", nullable=False)  # 'Manual', 'OCR_Extracted', 'Verified'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="prescriptions")
    medicines = relationship("PrescriptionMedicine", back_populates="prescription", cascade="all, delete-orphan")


class PrescriptionMedicine(Base):
    __tablename__ = "prescription_medicines"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_name = Column(String(100), nullable=False, index=True)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    duration = Column(String(100), nullable=True)
    instructions = Column(Text, nullable=True)

    prescription = relationship("Prescription", back_populates="medicines")


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    allergen = Column(String(100), nullable=False, index=True)
    reaction = Column(String(255), nullable=True)
    severity = Column(String(50), nullable=True)
    verification_status = Column(String(50), default="Self-Reported", nullable=False)  # 'Self-Reported', 'Clinically Verified'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    user = relationship("User", back_populates="allergies")


class DoctorBriefing(Base):
    __tablename__ = "doctor_briefings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    visit_reason = Column(Text, nullable=False)
    symptoms_summary = Column(Text, nullable=True)
    vitals_summary = Column(Text, nullable=True)
    allergies_summary = Column(Text, nullable=True)
    medicines_summary = Column(Text, nullable=True)
    questions_to_ask = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="briefings")
    shares = relationship("SharedBriefing", back_populates="briefing", cascade="all, delete-orphan")


class SharedBriefing(Base):
    __tablename__ = "shared_briefings"

    id = Column(Integer, primary_key=True, index=True)
    briefing_id = Column(Integer, ForeignKey("doctor_briefings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    share_token = Column(String(64), unique=True, index=True, nullable=False)
    recipient_name = Column(String(150), nullable=True)
    recipient_role = Column(String(50), default="Physician")
    access_pin = Column(String(20), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    briefing = relationship("DoctorBriefing", back_populates="shares")
    user = relationship("User")


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    medicine_name = Column(String(100), unique=True, index=True, nullable=False)
    generic_name = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    common_uses = Column(Text, nullable=True)
    contraindications = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)
    prescription_required = Column(Boolean, default=False)


class MedicineInteraction(Base):
    __tablename__ = "medicine_interactions"

    id = Column(Integer, primary_key=True, index=True)
    medicine_a = Column(String(100), index=True, nullable=False)
    medicine_b = Column(String(100), index=True, nullable=False)
    interaction_level = Column(String(50), nullable=False)  # High, Moderate, Minor
    description = Column(Text, nullable=True)


class LoginActivity(Base):
    __tablename__ = "login_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email = Column(String(255), index=True, nullable=False)
    name = Column(String(100), nullable=True)
    activity_type = Column(String(50), nullable=False)  # 'LOGIN' or 'REGISTER'
    status = Column(String(50), default="SUCCESS")       # 'SUCCESS' or 'FAILED'
    ip_address = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

