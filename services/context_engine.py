"""
Health Context Engine for HealthBridge AI
Unified clinical intelligence layer aggregating user-reported symptoms,
objective ML assessments, prescription vault documents, and documented allergies.
Strictly distinguishes current vs. historical records and avoids clinical hallucinations.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models import User, HealthAssessment, RecentProblem, Prescription, Allergy, DoctorBriefing

def get_patient_health_context(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Extracts and organizes the comprehensive, authenticated health context for a patient.
    Separates active records from historical archives.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}

    # 1. Latest Health Assessment & History
    assessments = db.query(HealthAssessment).filter(
        HealthAssessment.user_id == user_id
    ).order_by(desc(HealthAssessment.created_at)).all()
    latest_assessment = assessments[0] if assessments else None

    # 2. Symptoms & Health Problems (active vs resolved)
    problems = db.query(RecentProblem).filter(
        RecentProblem.user_id == user_id
    ).order_by(desc(RecentProblem.created_at)).all()
    
    active_problems = [p for p in problems if getattr(p, "status", "Active") == "Active"]
    resolved_problems = [p for p in problems if getattr(p, "status", "Active") != "Active"]

    # 3. Documented Allergies
    allergies = db.query(Allergy).filter(
        Allergy.user_id == user_id
    ).order_by(desc(Allergy.created_at)).all()

    # 4. Prescriptions & Medications (Active vs Historical)
    prescriptions = db.query(Prescription).filter(
        Prescription.user_id == user_id
    ).order_by(desc(Prescription.created_at)).all()

    all_medicines = []
    for rx in prescriptions:
        for m in rx.medicines:
            all_medicines.append({
                "medicine_name": m.medicine_name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "duration": m.duration,
                "instructions": m.instructions,
                "prescribed_date": rx.prescription_date.strftime("%Y-%m-%d") if rx.prescription_date else None,
                "doctor_name": rx.doctor_name,
                "main_problem": rx.main_health_problem or rx.diagnosis,
                "prescription_id": rx.id
            })

    return {
        "user_id": user.id,
        "patient_name": user.name,
        "patient_email": user.email,
        "latest_assessment": {
            "id": latest_assessment.id,
            "predicted_risk": latest_assessment.predicted_risk,
            "confidence": latest_assessment.confidence,
            "probabilities": latest_assessment.probabilities,
            "heart_rate": latest_assessment.heart_rate,
            "systolic_blood_pressure": latest_assessment.systolic_blood_pressure,
            "oxygen_saturation": latest_assessment.oxygen_saturation,
            "chest_pain_severity": latest_assessment.chest_pain_severity,
            "body_temperature": latest_assessment.body_temperature,
            "assessed_at": latest_assessment.created_at.isoformat() if latest_assessment.created_at else None
        } if latest_assessment else None,
        "total_assessments_count": len(assessments),
        "active_problems": [
            {
                "id": p.id,
                "text": p.problem_text,
                "category": p.problem_category,
                "severity": p.severity,
                "duration": p.duration,
                "status": getattr(p, "status", "Active"),
                "created_at": p.created_at.isoformat() if p.created_at else None
            } for p in active_problems
        ],
        "resolved_problems_count": len(resolved_problems),
        "allergies": [
            {
                "id": a.id,
                "allergen": a.allergen,
                "reaction": a.reaction,
                "severity": a.severity,
                "verification_status": getattr(a, "verification_status", "Self-Reported"),
                "created_at": a.created_at.isoformat() if getattr(a, "created_at", None) else None
            } for a in allergies
        ],
        "prescriptions_count": len(prescriptions),
        "current_medicines": all_medicines[:5], # Most recent
        "all_medicines": all_medicines
    }

def generate_doctor_briefing_draft(user_id: int, visit_reason: str, db: Session) -> Dict[str, Any]:
    """
    Synthesizes current patient records into a clear, professional Doctor-Visit Briefing draft.
    Does not provide definitive diagnosis. Outlines symptoms, vitals, allergies, and discussion questions.
    """
    ctx = get_patient_health_context(user_id, db)
    patient_name = ctx.get("patient_name", "Patient")
    
    # 1. Symptoms Summary
    active_probs = ctx.get("active_problems", [])
    if active_probs:
        symptom_bullets = [
            f"• {p['text']} (Reported Severity: {p.get('severity', 'Moderate')}, Duration: {p.get('duration', 'Unspecified')})"
            for p in active_probs
        ]
        symptoms_summary = "\n".join(symptom_bullets)
    else:
        symptoms_summary = "No acute active symptoms currently reported by patient."

    # 2. Vitals Summary
    latest = ctx.get("latest_assessment")
    if latest:
        vitals_summary = (
            f"• Resting Blood Pressure: {latest['systolic_blood_pressure']} mmHg\n"
            f"• Resting Heart Rate: {latest['heart_rate']} bpm\n"
            f"• Oxygen Saturation (SpO₂): {latest['oxygen_saturation']}%\n"
            f"• Body Temperature: {latest['body_temperature']} °C\n"
            f"• Chest Pain Score (0-10): {latest['chest_pain_severity']}\n"
            f"• AI Estimated Cardiovascular Risk: {latest['predicted_risk']} (Confidence: {latest['confidence']}%)\n"
            f"  [Note: Statistical machine learning screening estimate; requires clinical correlation.]"
        )
    else:
        vitals_summary = "No recent vital assessments recorded in the system."

    # 3. Allergies Summary
    allergies = ctx.get("allergies", [])
    if allergies:
        allergy_bullets = [
            f"• {a['allergen']}: {a.get('reaction') or 'Reaction not specified'} (Severity: {a.get('severity', 'Moderate')}, {a.get('verification_status', 'Self-Reported')})"
            for a in allergies
        ]
        allergies_summary = "\n".join(allergy_bullets)
    else:
        allergies_summary = "No drug or food allergies documented by patient."

    # 4. Medicines Summary
    meds = ctx.get("current_medicines", [])
    if meds:
        med_bullets = [
            f"• {m['medicine_name']} {m.get('dosage') or ''} - {m.get('frequency') or 'As directed'} (Rx Date: {m.get('prescribed_date') or 'Unspecified'}, Prescriber: Dr. {m.get('doctor_name') or 'Physician'})"
            for m in meds
        ]
        medicines_summary = "\n".join(med_bullets)
    else:
        medicines_summary = "No active prescription medications recorded in Prescription Vault."

    # 5. Suggested Questions for the Doctor
    questions = [
        f"1. How do my recent symptoms relate to my reason for visit: '{visit_reason}'?",
        "2. Are there any routine diagnostic screenings, blood tests, or ECGs recommended based on my vitals?",
        "3. Should my current prescription medications be continued, adjusted, or reviewed for interactions?",
        "4. What lifestyle modifications (dietary, physical activity) are safest for my cardiovascular profile?"
    ]
    if latest and latest.get("systolic_blood_pressure", 120) >= 140:
        questions.append("5. My recorded resting systolic blood pressure is elevated. What threshold warrants medication therapy?")
    if latest and latest.get("chest_pain_severity", 0) > 0:
        questions.append("6. What specific warning signs with my chest discomfort require immediate emergency medical care?")

    return {
        "title": f"Physician Briefing: {visit_reason[:60]}",
        "visit_reason": visit_reason,
        "symptoms_summary": symptoms_summary,
        "vitals_summary": vitals_summary,
        "allergies_summary": allergies_summary,
        "medicines_summary": medicines_summary,
        "questions_to_ask": "\n".join(questions),
        "notes": f"Prepared for {patient_name}'s clinical consultation. Inform clinician of any unrecorded over-the-counter supplements."
    }

def get_timeline_events(user_id: int, event_type: Optional[str], db: Session) -> List[Dict[str, Any]]:
    """
    Extracts all chronological health events across assessments, symptoms, prescriptions, allergies, and briefings.
    """
    events: List[Dict[str, Any]] = []

    # 1. Assessments
    if not event_type or event_type.upper() in ["ASSESSMENT", "ALL"]:
        assessments = db.query(HealthAssessment).filter(HealthAssessment.user_id == user_id).all()
        for a in assessments:
            date_val = a.created_at or datetime.now(timezone.utc)
            events.append({
                "id": f"assess_{a.id}",
                "event_type": "ASSESSMENT",
                "title": f"Health Risk Assessment: {a.predicted_risk}",
                "description": f"Model confidence: {a.confidence}%. BP: {a.systolic_blood_pressure} mmHg, HR: {a.heart_rate} bpm, SpO₂: {a.oxygen_saturation}%.",
                "event_date": date_val,
                "badge": a.predicted_risk,
                "severity": "High" if "High" in a.predicted_risk or "Crit" in a.predicted_risk else "Moderate" if "Mod" in a.predicted_risk else "Low",
                "metadata": {
                    "risk_level": a.predicted_risk,
                    "confidence": a.confidence,
                    "blood_pressure": a.systolic_blood_pressure,
                    "heart_rate": a.heart_rate,
                    "chest_pain": a.chest_pain_severity
                },
                "source_id": a.id,
                "source_link": f"history.html"
            })

    # 2. Symptoms & Problems
    if not event_type or event_type.upper() in ["SYMPTOM", "ALL"]:
        problems = db.query(RecentProblem).filter(RecentProblem.user_id == user_id).all()
        for p in problems:
            date_val = p.created_at or datetime.now(timezone.utc)
            events.append({
                "id": f"prob_{p.id}",
                "event_type": "SYMPTOM",
                "title": f"Symptom Log: {p.problem_category or 'General Symptom'}",
                "description": p.problem_text,
                "event_date": date_val,
                "badge": getattr(p, "status", "Active"),
                "severity": p.severity or "Moderate",
                "metadata": {
                    "severity": p.severity,
                    "duration": p.duration,
                    "category": p.problem_category,
                    "status": getattr(p, "status", "Active")
                },
                "source_id": p.id,
                "source_link": f"problems.html"
            })

    # 3. Prescriptions
    if not event_type or event_type.upper() in ["PRESCRIPTION", "ALL"]:
        prescriptions = db.query(Prescription).filter(Prescription.user_id == user_id).all()
        for rx in prescriptions:
            date_val = rx.prescription_date or rx.created_at or datetime.now(timezone.utc)
            med_names = [m.medicine_name for m in rx.medicines]
            desc = f"Doctor: Dr. {rx.doctor_name or 'Unspecified'} | Problem: {rx.main_health_problem or rx.diagnosis or 'Clinical Consultation'}"
            if med_names:
                desc += f" | Medications: {', '.join(med_names)}"
            events.append({
                "id": f"rx_{rx.id}",
                "event_type": "PRESCRIPTION",
                "title": f"Prescription: {rx.main_health_problem or 'Medical Record'}",
                "description": desc,
                "event_date": date_val,
                "badge": getattr(rx, "extraction_status", "Manual"),
                "severity": "Info",
                "metadata": {
                    "doctor": rx.doctor_name,
                    "hospital": rx.hospital_name,
                    "medicine_count": len(rx.medicines),
                    "has_file": bool(rx.file_path)
                },
                "source_id": rx.id,
                "source_link": f"prescription.html"
            })

    # 4. Allergies
    if not event_type or event_type.upper() in ["ALLERGY", "ALL"]:
        allergies = db.query(Allergy).filter(Allergy.user_id == user_id).all()
        for a in allergies:
            date_val = getattr(a, "created_at", None) or datetime.now(timezone.utc)
            events.append({
                "id": f"allg_{a.id}",
                "event_type": "ALLERGY",
                "title": f"Allergy Documented: {a.allergen}",
                "description": f"Reported Reaction: {a.reaction or 'Sensory/systemic'} (Severity: {a.severity or 'Moderate'}).",
                "event_date": date_val,
                "badge": getattr(a, "verification_status", "Self-Reported"),
                "severity": a.severity or "Moderate",
                "metadata": {
                    "allergen": a.allergen,
                    "reaction": a.reaction,
                    "severity": a.severity
                },
                "source_id": a.id,
                "source_link": f"allergies.html"
            })

    # 5. Doctor Briefings
    if not event_type or event_type.upper() in ["BRIEFING", "ALL"]:
        briefings = db.query(DoctorBriefing).filter(DoctorBriefing.user_id == user_id).all()
        for b in briefings:
            date_val = b.created_at or datetime.now(timezone.utc)
            events.append({
                "id": f"brief_{b.id}",
                "event_type": "BRIEFING",
                "title": f"Doctor Briefing: {b.title}",
                "description": f"Visit Reason: {b.visit_reason}",
                "event_date": date_val,
                "badge": "Clinical Summary",
                "severity": "Info",
                "metadata": {
                    "title": b.title,
                    "shares_count": len(b.shares)
                },
                "source_id": b.id,
                "source_link": f"briefing.html"
            })

    def _to_naive(dt):
        if not dt:
            return datetime.min
        if getattr(dt, "tzinfo", None) is not None:
            return dt.replace(tzinfo=None)
        return dt

    # Sort descending by date
    events.sort(key=lambda e: _to_naive(e["event_date"]), reverse=True)
    return events
