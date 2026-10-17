"""
Health Context Engine for HealthBridge AI
Unified clinical intelligence layer aggregating user-reported symptoms,
objective ML assessments, prescription vault documents, and documented allergies.
Strictly distinguishes current vs. historical records and avoids clinical hallucinations.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

logger = logging.getLogger("health_risk_system")

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

def _normalize_datetime(val: Any) -> datetime:
    """Safely converts string, date, or datetime into a naive UTC-equivalent datetime for uniform sorting."""
    if val is None:
        return datetime.min
    if isinstance(val, str):
        try:
            val = datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            try:
                val = datetime.strptime(val[:10], "%Y-%m-%d")
            except Exception:
                return datetime.min
    elif isinstance(val, datetime):
        pass
    elif hasattr(val, "year") and hasattr(val, "month") and hasattr(val, "day"):
        # date object
        val = datetime.combine(val, datetime.min.time())
    else:
        return datetime.min

    if getattr(val, "tzinfo", None) is not None:
        return val.replace(tzinfo=None)
    return val

def get_timeline_events(user_id: int, event_type: Optional[str], db: Session) -> List[Dict[str, Any]]:
    """
    Extracts all chronological health events across assessments, symptoms, prescriptions, allergies, and briefings.
    Includes per-record fault tolerance so one malformed record cannot crash the entire user timeline.
    """
    events: List[Dict[str, Any]] = []
    clean_filter = (event_type or "").strip().upper()

    # 1. Assessments
    if not clean_filter or clean_filter in ["ASSESSMENT", "ALL"]:
        try:
            assessments = db.query(HealthAssessment).filter(HealthAssessment.user_id == user_id).all()
            for a in assessments:
                try:
                    date_val = a.created_at or datetime.now(timezone.utc)
                    risk_str = str(a.predicted_risk or "Assessment Recorded")
                    severity = "High" if ("High" in risk_str or "Crit" in risk_str) else ("Moderate" if "Mod" in risk_str else "Low")
                    events.append({
                        "id": f"assess_{a.id}",
                        "event_type": "ASSESSMENT",
                        "title": f"Health Risk Assessment: {risk_str}",
                        "description": f"Model confidence: {a.confidence or 0}%. BP: {a.systolic_blood_pressure or 0} mmHg, HR: {a.heart_rate or 0} bpm, SpO₂: {a.oxygen_saturation or 0}%.",
                        "event_date": _normalize_datetime(date_val),
                        "badge": risk_str,
                        "severity": severity,
                        "metadata": {
                            "risk_level": risk_str,
                            "confidence": a.confidence,
                            "blood_pressure": a.systolic_blood_pressure,
                            "heart_rate": a.heart_rate,
                            "chest_pain": a.chest_pain_severity
                        },
                        "source_id": a.id,
                        "source_link": "history.html"
                    })
                except Exception as rec_err:
                    logger.warning(f"[Timeline] Skipped assessment record #{getattr(a, 'id', '?')} due to parsing error: {rec_err}")
        except Exception as q_err:
            logger.error(f"[Timeline] Query failed for assessments (user {user_id}): {q_err}")

    # 2. Symptoms & Problems
    if not clean_filter or clean_filter in ["SYMPTOM", "ALL"]:
        try:
            problems = db.query(RecentProblem).filter(RecentProblem.user_id == user_id).all()
            for p in problems:
                try:
                    date_val = p.created_at or datetime.now(timezone.utc)
                    status_val = str(getattr(p, "status", None) or "Active")
                    events.append({
                        "id": f"prob_{p.id}",
                        "event_type": "SYMPTOM",
                        "title": f"Symptom Log: {p.problem_category or 'General Symptom'}",
                        "description": str(p.problem_text or "Recorded symptom description"),
                        "event_date": _normalize_datetime(date_val),
                        "badge": status_val,
                        "severity": p.severity or "Moderate",
                        "metadata": {
                            "severity": p.severity,
                            "duration": p.duration,
                            "category": p.problem_category,
                            "status": status_val
                        },
                        "source_id": p.id,
                        "source_link": "problems.html"
                    })
                except Exception as rec_err:
                    logger.warning(f"[Timeline] Skipped problem record #{getattr(p, 'id', '?')} due to parsing error: {rec_err}")
        except Exception as q_err:
            logger.error(f"[Timeline] Query failed for symptoms (user {user_id}): {q_err}")

    # 3. Prescriptions
    if not clean_filter or clean_filter in ["PRESCRIPTION", "ALL"]:
        try:
            prescriptions = (
                db.query(Prescription)
                .options(joinedload(Prescription.medicines))
                .filter(Prescription.user_id == user_id)
                .all()
            )
            for rx in prescriptions:
                try:
                    date_val = rx.prescription_date or rx.created_at or datetime.now(timezone.utc)
                    meds = getattr(rx, "medicines", []) or []
                    med_names = [m.medicine_name for m in meds if getattr(m, "medicine_name", None)]
                    desc = f"Doctor: Dr. {rx.doctor_name or 'Unspecified'} | Problem: {rx.main_health_problem or rx.diagnosis or 'Clinical Consultation'}"
                    if med_names:
                        desc += f" | Medications: {', '.join(med_names)}"
                    events.append({
                        "id": f"rx_{rx.id}",
                        "event_type": "PRESCRIPTION",
                        "title": f"Prescription: {rx.main_health_problem or rx.title or 'Medical Record'}",
                        "description": desc,
                        "event_date": _normalize_datetime(date_val),
                        "badge": getattr(rx, "extraction_status", None) or "Manual",
                        "severity": "Info",
                        "metadata": {
                            "doctor": rx.doctor_name,
                            "hospital": rx.hospital_name,
                            "medicine_count": len(meds),
                            "has_file": bool(rx.file_path)
                        },
                        "source_id": rx.id,
                        "source_link": "prescription.html"
                    })
                except Exception as rec_err:
                    logger.warning(f"[Timeline] Skipped prescription record #{getattr(rx, 'id', '?')} due to parsing error: {rec_err}")
        except Exception as q_err:
            logger.error(f"[Timeline] Query failed for prescriptions (user {user_id}): {q_err}")

    # 4. Allergies
    if not clean_filter or clean_filter in ["ALLERGY", "ALL"]:
        try:
            allergies = db.query(Allergy).filter(Allergy.user_id == user_id).all()
            for a in allergies:
                try:
                    date_val = getattr(a, "created_at", None) or datetime.now(timezone.utc)
                    events.append({
                        "id": f"allg_{a.id}",
                        "event_type": "ALLERGY",
                        "title": f"Allergy Documented: {a.allergen or 'Unknown allergen'}",
                        "description": f"Reported Reaction: {a.reaction or 'Sensory/systemic'} (Severity: {a.severity or 'Moderate'}).",
                        "event_date": _normalize_datetime(date_val),
                        "badge": getattr(a, "verification_status", None) or "Self-Reported",
                        "severity": a.severity or "Moderate",
                        "metadata": {
                            "allergen": a.allergen,
                            "reaction": a.reaction,
                            "severity": a.severity
                        },
                        "source_id": a.id,
                        "source_link": "allergies.html"
                    })
                except Exception as rec_err:
                    logger.warning(f"[Timeline] Skipped allergy record #{getattr(a, 'id', '?')} due to parsing error: {rec_err}")
        except Exception as q_err:
            logger.error(f"[Timeline] Query failed for allergies (user {user_id}): {q_err}")

    # 5. Doctor Briefings
    if not clean_filter or clean_filter in ["BRIEFING", "ALL"]:
        try:
            briefings = (
                db.query(DoctorBriefing)
                .options(joinedload(DoctorBriefing.shares))
                .filter(DoctorBriefing.user_id == user_id)
                .all()
            )
            for b in briefings:
                try:
                    date_val = b.created_at or datetime.now(timezone.utc)
                    shares = getattr(b, "shares", []) or []
                    events.append({
                        "id": f"brief_{b.id}",
                        "event_type": "BRIEFING",
                        "title": f"Doctor Briefing: {b.title or 'Consultation Briefing'}",
                        "description": f"Visit Reason: {b.visit_reason or 'Clinical Review'}",
                        "event_date": _normalize_datetime(date_val),
                        "badge": "Clinical Summary",
                        "severity": "Info",
                        "metadata": {
                            "title": b.title,
                            "shares_count": len(shares)
                        },
                        "source_id": b.id,
                        "source_link": "briefing.html"
                    })
                except Exception as rec_err:
                    logger.warning(f"[Timeline] Skipped briefing record #{getattr(b, 'id', '?')} due to parsing error: {rec_err}")
        except Exception as q_err:
            logger.error(f"[Timeline] Query failed for briefings (user {user_id}): {q_err}")

    # Sort descending by date (safely using normalized datetime)
    events.sort(key=lambda e: _normalize_datetime(e.get("event_date")), reverse=True)
    return events
