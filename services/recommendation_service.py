from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from database.models import User, Medicine, HealthAssessment, RecentProblem, Prescription, PrescriptionMedicine, Allergy
from services.medicine_safety import screen_candidate_medicine

def build_personalized_recommendations(
    patient_data: dict,
    risk_level: str,
    confidence: float,
    probabilities: dict,
    user: Optional[User] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Core Recommendation Engine:
    Combines Current Health Inputs & Actual ML Risk with:
    - Recent Problems from DB
    - Previous Health Assessments & Vitals History
    - Previous Prescriptions & Prescription Medicines from DB
    - Patient Allergies from DB
    - Clinical Medicine Information & Interaction Layer
    Produces complete, tailored guidance decoupled from the ML pipeline.
    """
    do_list: List[str] = []
    avoid_list: List[str] = []
    safety_warnings: List[str] = []
    discussion_points: List[str] = []

    # 1. Extract clinical vitals
    age = int(patient_data.get("age", 45) or 45)
    gender = str(patient_data.get("gender", "Unspecified")).strip().title()
    has_smoker = str(patient_data.get("smoker_status", "")).strip().lower() in ["yes", "y", "true", "1"]
    has_diabetes = str(patient_data.get("diabetes_history", "")).strip().lower() in ["yes", "y", "true", "1"]
    sbp = float(patient_data.get("systolic_blood_pressure", 120) or 120)
    hr = float(patient_data.get("heart_rate", 75) or 75)
    o2 = float(patient_data.get("oxygen_saturation", 98) or 98)
    chest_pain = float(patient_data.get("chest_pain_severity", 0) or 0)
    temp = float(patient_data.get("body_temperature", 36.8) or 36.8)

    # 2. Extract user historical context from DB if user is provided
    recent_problems_list: List[str] = []
    recent_problem_categories: List[str] = []
    historical_medicines_list: List[str] = []
    previous_prescriptions_list: List[str] = []
    allergies_list: List[str] = []
    known_conditions: List[str] = []

    if has_diabetes:
        known_conditions.append("Diabetes")
    if sbp >= 140:
        known_conditions.append("Hypertension")

    if user:
        if user.problems:
            for p in user.problems:
                recent_problems_list.append(p.problem_text)
                if p.problem_category:
                    recent_problem_categories.append(p.problem_category)

        if user.prescriptions:
            for presc in user.prescriptions:
                diag = presc.main_health_problem or presc.diagnosis or "Prescription"
                p_date = presc.prescription_date.strftime("%Y-%m-%d") if presc.prescription_date else "Date unrecorded"
                doc = presc.doctor_name or "Unspecified Doctor"
                previous_prescriptions_list.append(f"{diag} ({p_date}, Dr. {doc})")
                for med in presc.medicines:
                    if med.medicine_name:
                        historical_medicines_list.append(med.medicine_name.strip())

        if user.allergies:
            for a in user.allergies:
                allergies_list.append(a.allergen.strip())

    # De-duplicate lists
    historical_medicines_list = list(dict.fromkeys(historical_medicines_list))
    allergies_list = list(dict.fromkeys(allergies_list))

    # 3. Emergency Safety Screening (Immediate Triaging)
    emergency_warning: Optional[str] = None
    has_critical_chest_pain = chest_pain >= 7
    has_critical_o2 = o2 < 90
    has_high_urgency_dyspnea = (o2 < 94 and chest_pain >= 5)
    has_extreme_hr = hr < 40 or hr > 140
    is_critical_risk = "crit" in risk_level.lower()

    # Check if recent problems describe acute emergencies
    problem_text_blob = " ".join(recent_problems_list).lower()
    has_acute_complaint = any(k in problem_text_blob for k in ["crushing chest", "fainted", "unconscious", "cannot breathe", "severe pressure"])

    if has_critical_chest_pain or has_critical_o2 or has_high_urgency_dyspnea or has_extreme_hr or is_critical_risk or has_acute_complaint:
        emergency_warning = (
            "URGENT EMERGENCY CARE RECOMMENDED: Critical cardiovascular or respiratory indicators detected "
            f"(Chest Pain: {chest_pain}/10, O2 Saturation: {o2}%, Heart Rate: {hr} bpm). "
            "Please seek immediate emergency medical evaluation or call local emergency services immediately. "
            "Do not delay care or rely solely on algorithmic risk estimates."
        )

    # 4. Doctor Recommendation Logic (Specialist determination)
    rec_specialist = "Primary Care Physician"
    rec_urgency = "Routine Scheduled Follow-up"
    specialist_reason = "A primary healthcare evaluation is appropriate for preventive review of cardiovascular risk factors and routine blood work."

    if emergency_warning:
        rec_specialist = "Emergency Medical Evaluation"
        rec_urgency = "Immediate / Emergency"
        specialist_reason = "Consider seeking an immediate in-person evaluation by an emergency medical physician due to acute physiological or symptom indicators."
        discussion_points.append(f"Immediate evaluation of acute chest pain severity ({chest_pain}/10) and vital instability")
        discussion_points.append("Electrocardiogram (ECG) and cardiac biomarker enzyme panel (Troponin)")
    elif is_critical_risk or "high" in risk_level.lower() or sbp >= 160 or chest_pain >= 4 or "Cardiovascular" in recent_problem_categories or any(k in problem_text_blob for k in ["chest discomfort", "chest pain", "angina"]):
        rec_specialist = "Cardiologist"
        rec_urgency = "Prompt Consultation (Within 24-48 Hours)"
        specialist_reason = "Consider discussing your elevated cardiovascular risk profile, blood pressure, and chest symptoms with a specialist in cardiology."
        discussion_points.append(f"Review of resting blood pressure ({sbp} mmHg) and heart rate ({hr} bpm)")
        discussion_points.append("Comprehensive echocardiogram and exercise stress testing evaluation")
        discussion_points.append("Cardioprotective medication optimization (statin / antihypertensive therapy)")
    elif o2 < 94 or "Respiratory" in recent_problem_categories or any(k in problem_text_blob for k in ["shortness of breath", "breath", "wheez", "cough"]):
        rec_specialist = "Pulmonologist"
        rec_urgency = "Timely Consultation (Within 1-2 Weeks)"
        specialist_reason = "Consider discussing your oxygen saturation levels and reported respiratory discomfort with a pulmonologist."
        discussion_points.append(f"Investigation of oxygen saturation ({o2}%) during resting and ambulatory states")
        discussion_points.append("Pulmonary function testing (spirometry) and chest radiography")
    elif has_diabetes or "Endocrine" in recent_problem_categories or any(k in problem_text_blob for k in ["glucose", "sugar", "insulin"]):
        rec_specialist = "Endocrinologist"
        rec_urgency = "Timely Consultation (Within 1-2 Weeks)"
        specialist_reason = "Consider discussing your metabolic glycemic control and cardiovascular risk with an endocrinologist."
        discussion_points.append("Hemoglobin A1c (HbA1c) level review and glycemic monitoring log")
        discussion_points.append("Cardiovascular-protective antidiabetic pharmacotherapy review")
    elif "mod" in risk_level.lower():
        rec_specialist = "Primary Care Physician"
        rec_urgency = "Timely Consultation (Within 2-4 Weeks)"
        specialist_reason = "Consider discussing your moderate cardiovascular risk profile and lifestyle modification goals with a primary care physician."
        discussion_points.append("Fasting lipid panel (total cholesterol, LDL, HDL, triglycerides)")
        discussion_points.append("Blood pressure baseline monitoring protocol")
    else:
        rec_specialist = "Primary Care Physician"
        rec_urgency = "Routine Preventive Check-up"
        specialist_reason = "Consider discussing your routine cardiovascular wellness, risk metrics, and preventive lifestyle strategies with a primary care physician."
        discussion_points.append("General wellness and preventive cardiovascular maintenance")

    # 5. What You Should Do (Personalized Actions)
    do_list.append("Schedule a comprehensive health evaluation to discuss these AI-assisted screening findings.")
    do_list.append("Maintain consistent daily tracking of resting blood pressure and heart rate.")

    if sbp >= 140:
        do_list.append(f"Discuss your systolic blood pressure reading of {sbp} mmHg with your healthcare provider.")
        do_list.append("Adopt heart-healthy dietary habits such as the DASH or Mediterranean eating plan, emphasizing fresh fruits, vegetables, and whole grains.")

    if has_smoker:
        do_list.append("Ask your physician about structured smoking-cessation resources, nicotine replacement, or behavioral counseling.")

    if has_diabetes:
        do_list.append("Maintain doctor-supervised glycemic control, taking blood glucose measurements at prescribed intervals.")

    # Tailoring based on Recent Problems
    if any(k in problem_text_blob for k in ["chest discomfort", "chest pain", "tightness", "angina"]):
        do_list.append("Keep a strict log of chest discomfort occurrences, noting duration, physical triggers, and whether rest provides relief.")
        do_list.append("Discuss your recent chest discomfort directly with your doctor; seek urgent evaluation if it radiates to your jaw, neck, or left arm.")

    if any(k in problem_text_blob for k in ["shortness of breath", "breath", "dyspnea", "wheez"]):
        do_list.append("Record any episodes of shortness of breath during exertion versus rest, and share these observations with your healthcare provider.")

    if recent_problems_list and not any(k in problem_text_blob for k in ["chest", "breath"]):
        do_list.append(f"Discuss the progression and pattern of your logged symptom: '{recent_problems_list[0][:80]}' with your physician.")

    # Tailoring based on Prescriptions & Clinical History
    if historical_medicines_list:
        do_list.append(f"Bring your recorded medication history ({', '.join(historical_medicines_list[:4])}) to your consultation for continuity of care.")
        do_list.append("Discuss with your physician which historical medications should be actively continued, discontinued, or replaced.")

    if previous_prescriptions_list:
        do_list.append(f"Bring documentation of your treatment history ({', '.join(previous_prescriptions_list[:2])}) to your consultation for continuity of care.")

    do_list.append("Engage in moderate-intensity physical activity (e.g., 30 minutes of walking) as cleared by your physician.")

    # 6. What You Should Avoid (Precautions)
    avoid_list.append("Do NOT use this AI risk prediction as a definitive medical diagnosis or replacement for a physician.")
    avoid_list.append("Do NOT automatically restart, stop, or alter your medications based on historical prescription records without direct physician orders.")

    if sbp >= 130:
        avoid_list.append("Avoid excessive dietary sodium (aim for under 2,000 mg/day unless clinically advised otherwise) and ultra-processed foods.")
        avoid_list.append("Avoid energy drinks, excessive caffeine, and stimulant decongestants that can acutely elevate blood pressure.")

    if has_smoker:
        avoid_list.append("Avoid active smoking and exposure to secondhand tobacco smoke or vapor.")

    if chest_pain >= 3 or recent_problems_list:
        avoid_list.append("Avoid strenuous physical exertion, heavy lifting, or unaccustomed vigorous exercise until cleared by a physician.")

    if emergency_warning:
        avoid_list.append("Do NOT drive yourself to the hospital or delay seeking emergency medical evaluation if chest pressure, shortness of breath, or dizziness worsens.")

    # 7. Medicine Information & Safety Screening Layer
    screened_medicines: List[Dict[str, Any]] = []

    # Select candidate cardiovascular/metabolic medicines from database to review
    candidate_names = ["Aspirin", "Atorvastatin"]
    if is_critical_risk or "high" in risk_level.lower():
        candidate_names.extend(["Metoprolol", "Amlodipine"])
    elif "mod" in risk_level.lower() or sbp >= 140:
        candidate_names.extend(["Lisinopril", "Amlodipine"])

    if has_diabetes:
        candidate_names.append("Metformin")

    # Include any medicines the user has historically been prescribed for safety continuity review
    for hm in historical_medicines_list:
        if hm not in candidate_names:
            candidate_names.append(hm)

    # If user has recorded allergies, include any matching medicines to screen for direct allergy conflicts
    if db and allergies_list:
        for al in allergies_list:
            matched_med = db.query(Medicine).filter(Medicine.medicine_name.ilike(al.strip())).first()
            if matched_med and matched_med.medicine_name not in candidate_names:
                candidate_names.append(matched_med.medicine_name)

    candidate_names = list(dict.fromkeys(candidate_names))

    if db:
        for med_name in candidate_names:
            med_record = db.query(Medicine).filter(Medicine.medicine_name.ilike(med_name.strip())).first()
            if not med_record:
                continue

            # Clinical rationale for discussing this medicine
            clinical_reason = f"Candidate cardioprotective/supportive therapy indicated for clinician discussion based on risk tier and clinical markers."
            if med_record.medicine_name in historical_medicines_list:
                clinical_reason = f"Historically documented medication ({med_record.medicine_name}) in patient vault. Flagged for clinician continuity review (not an active automatic prescription)."
            elif med_record.medicine_name == "Metformin":
                clinical_reason = "Consider discussing glycemic management and metabolic therapy with an endocrinologist."
            elif med_record.medicine_name == "Atorvastatin":
                clinical_reason = "Consider discussing lipid panel review and primary/secondary cardiovascular prevention."
            elif med_record.medicine_name in ["Metoprolol", "Amlodipine", "Lisinopril"]:
                clinical_reason = f"Antihypertensive therapy candidate for discussion with clinician regarding blood pressure ({sbp} mmHg)."

            # Screen medicine against patient-specific historical context
            screened_item = screen_candidate_medicine(
                med_record=med_record,
                user_allergies=allergies_list,
                current_medicines=historical_medicines_list,
                user_conditions=known_conditions,
                recent_problems_text=recent_problems_list,
                clinical_reason=clinical_reason,
                db=db
            )
            screened_medicines.append(screened_item)

            if screened_item.get("warning"):
                safety_warnings.append(screened_item["warning"])

    # Unique safety warnings
    safety_warnings = list(dict.fromkeys(safety_warnings))

    doctor_rec_out = {
        "recommended_specialist": rec_specialist,
        "urgency": rec_urgency,
        "reason": specialist_reason,
        "discussion_points": list(dict.fromkeys(discussion_points))
    }

    patient_context_used = {
        "recent_problems_count": len(recent_problems_list),
        "previous_prescriptions_count": len(previous_prescriptions_list),
        "active_allergies_count": len(allergies_list),
        "recent_symptoms_considered": recent_problems_list[:3],
        "historical_medicines_considered": historical_medicines_list,
        "current_medicines_considered": historical_medicines_list
    }

    return {
        "risk_level": risk_level,
        "confidence": round(float(confidence), 1),
        "probabilities": probabilities,
        "what_to_do": list(dict.fromkeys(do_list)),
        "what_not_to_do": list(dict.fromkeys(avoid_list)),
        "doctor_recommendation": doctor_rec_out,
        "medicine_information": screened_medicines,
        "safety_warnings": safety_warnings,
        "emergency_warning": emergency_warning,
        "patient_context_used": patient_context_used,
        "disclaimer": (
            "Clinical guidance and medicine screening are provided solely for educational reference and discussion "
            "with a licensed healthcare professional. Never discontinue, start, or modify prescribed treatments without doctor consultation."
        )
    }

# Backward-compatible wrapper
def generate_recommendations(patient: dict, risk_level: str) -> Dict[str, Any]:
    res = build_personalized_recommendations(
        patient_data=patient,
        risk_level=risk_level,
        confidence=100.0,
        probabilities={},
        user=None,
        db=None
    )
    return {
        "risk_level": risk_level,
        "what_to_do": res["what_to_do"],
        "what_not_to_do": res["what_not_to_do"],
        "what_to_avoid": res["what_not_to_do"],
        "doctor": res["doctor_recommendation"]["reason"],
        "doctor_guidance": res["doctor_recommendation"]["reason"],
        "emergency_warning": res["emergency_warning"]
    }

def generate_medications_guidance(patient: dict, risk_level: str) -> List[str]:
    res = build_personalized_recommendations(
        patient_data=patient,
        risk_level=risk_level,
        confidence=100.0,
        probabilities={},
        user=None,
        db=None
    )
    return [m["reason"] for m in res["medicine_information"]]
