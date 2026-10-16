from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.models import Medicine, MedicineInteraction, Allergy, Prescription, PrescriptionMedicine

# Curated Clinical Knowledge Base for safety fallback and rapid rule matching
KNOWLEDGE_INTERACTIONS = {
    ("aspirin", "ibuprofen"): {
        "level": "Moderate",
        "desc": "Ibuprofen may inhibit the antiplatelet cardioprotective effect of low-dose aspirin and increase gastrointestinal bleeding risk."
    },
    ("aspirin", "warfarin"): {
        "level": "High",
        "desc": "Concomitant antithrombotic therapy significantly elevates the risk of severe systemic hemorrhage."
    },
    ("aspirin", "clopidogrel"): {
        "level": "Moderate",
        "desc": "Dual antiplatelet therapy provides augmented platelet inhibition but carries increased bleeding risk; requires close physician monitoring."
    },
    ("metoprolol", "amlodipine"): {
        "level": "Minor",
        "desc": "Additive blood pressure reduction and potential for symptomatic bradycardia. Monitor vital signs."
    },
    ("lisinopril", "ibuprofen"): {
        "level": "Moderate",
        "desc": "NSAIDs can blunt the antihypertensive efficacy of ACE inhibitors and precipitate acute kidney injury."
    },
    ("lisinopril", "losartan"): {
        "level": "High",
        "desc": "Dual renin-angiotensin system blockade significantly increases risks of hyperkalemia, acute kidney injury, and hypotension."
    },
    ("warfarin", "ibuprofen"): {
        "level": "High",
        "desc": "Extreme risk of gastrointestinal mucosal erosion and life-threatening bleeding."
    },
    ("nitroglycerin", "sildenafil"): {
        "level": "Critical",
        "desc": "Concomitant nitrate and PDE-5 inhibitor use causes profound, potentially fatal vasodilatory hypotension."
    }
}

KNOWLEDGE_CONTRAINDICATIONS = {
    "aspirin": ["peptic ulcer", "bleeding disorder", "hemophilia", "active bleed", "gastritis", "severe asthma"],
    "ibuprofen": ["kidney disease", "severe renal failure", "peptic ulcer", "asthma", "heart failure", "gastrointestinal bleed"],
    "metoprolol": ["severe bradycardia", "heart block", "cardiogenic shock", "decompensated heart failure", "hypotension"],
    "lisinopril": ["angioedema", "pregnancy", "bilateral renal artery stenosis", "hyperkalemia"],
    "amlodipine": ["severe hypotension", "cardiogenic shock", "aortic stenosis"],
    "warfarin": ["pregnancy", "active bleeding", "hemorrhagic stroke", "severe hepatic disease", "severe thrombocytopenia"],
    "nitroglycerin": ["severe anemia", "increased intracranial pressure", "pde-5 inhibitors", "severe hypotension"],
    "metformin": ["severe renal impairment", "kidney failure", "metabolic acidosis", "lactic acidosis", "severe hepatic impairment"],
    "losartan": ["pregnancy", "hyperkalemia", "aliskiren in diabetes"],
    "clopidogrel": ["active pathological bleeding", "peptic ulcer", "intracranial hemorrhage"]
}

def screen_candidate_medicine(
    med_record: Medicine,
    user_allergies: List[str],
    current_medicines: List[str],
    user_conditions: List[str],
    recent_problems_text: List[str],
    clinical_reason: str,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Screens a candidate medicine against patient-specific historical context:
    1. Allergy check (recorded allergies)
    2. Current & previous medicines (drug-drug interactions)
    3. Health conditions & recent problems (contraindications)
    4. Prescription history status
    Returns structured safety attributes adhering strictly to clinical safety guidelines.
    """
    med_name = med_record.medicine_name
    med_name_clean = med_name.strip()
    med_lower = med_name_clean.lower()
    generic_lower = (med_record.generic_name or "").lower()
    category_lower = (med_record.category or "").lower()

    potential_conflict = False
    warning_notes: List[str] = []

    # 1. Allergy Screening
    for allergen in user_allergies:
        all_clean = allergen.strip().lower()
        if (all_clean in med_lower or med_lower in all_clean or
            all_clean in generic_lower or generic_lower in all_clean or
            all_clean in category_lower):
            potential_conflict = True
            msg = f"Allergy Alert: Patient has recorded allergy to '{allergen}', which directly conflicts with {med_name_clean}."
            warning_notes.append(msg)

    # 2. Drug Interaction Screening against current/previous medications
    for other_med in current_medicines:
        other_clean = other_med.strip()
        other_lower = other_clean.lower()
        if other_lower == med_lower or other_lower == generic_lower:
            # Patient is already taking this medication
            clinical_reason = f"Patient has an existing prescription history for {med_name_clean}. Continue strictly as directed by prescribing physician."
            continue

        # Check Database Interactions
        db_inter = None
        if db:
            db_inter = db.query(MedicineInteraction).filter(
                or_(
                    (MedicineInteraction.medicine_a.ilike(med_name_clean)) & (MedicineInteraction.medicine_b.ilike(other_clean)),
                    (MedicineInteraction.medicine_a.ilike(other_clean)) & (MedicineInteraction.medicine_b.ilike(med_name_clean))
                )
            ).first()

        if db_inter:
            potential_conflict = True
            msg = f"Potential Drug Interaction ({db_inter.interaction_level}): {med_name_clean} + {other_clean} - {db_inter.description}"
            warning_notes.append(msg)
        else:
            # Check Knowledge Base interactions
            p1 = (med_lower, other_lower)
            p2 = (other_lower, med_lower)
            kb_inter = KNOWLEDGE_INTERACTIONS.get(p1) or KNOWLEDGE_INTERACTIONS.get(p2)
            if kb_inter:
                potential_conflict = True
                msg = f"Potential Drug Interaction ({kb_inter['level']}): {med_name_clean} + {other_clean} - {kb_inter['desc']}"
                warning_notes.append(msg)

    # 3. Conditions & Recent Problems Contraindication Screening
    contra_list = KNOWLEDGE_CONTRAINDICATIONS.get(med_lower, [])
    if med_record.contraindications:
        db_contras = [c.strip().lower() for c in med_record.contraindications.split(",") if c.strip()]
        contra_list = list(set(contra_list + db_contras))

    # Combine known conditions and recent problem texts
    all_health_context = [c.lower() for c in user_conditions] + [p.lower() for p in recent_problems_text]
    for ctx in all_health_context:
        for contra in contra_list:
            if not contra:
                continue
            # Match if contraindication appears in text or significant condition matches
            if contra in ctx or (len(ctx) >= 4 and ctx in contra):
                potential_conflict = True
                msg = f"Clinical Caution: '{med_name_clean}' has known contraindications/cautions associated with '{contra}'."
                warning_notes.append(msg)

    warning_text = " | ".join(list(dict.fromkeys(warning_notes))) if warning_notes else None

    return {
        "medicine_name": med_record.medicine_name,
        "generic_name": med_record.generic_name,
        "category": med_record.category,
        "common_uses": med_record.common_uses,
        "warnings": med_record.warnings,
        "contraindications": med_record.contraindications,
        "prescription_required": bool(med_record.prescription_required),
        "safe_to_display": True,  # Displayed transparently with screening flags
        "potential_conflict": potential_conflict,
        "warning": warning_text,
        "reason": clinical_reason,
        "requires_professional_review": True,
        "verified_database_record": True,
        "interaction_screening_note": (
            "Screened against verified interaction catalog. Screening is limited to cataloged entries "
            "and is not exhaustive; absence of a documented conflict does not establish clinical safety."
        )
    }


def check_medicine_safety(
    medicine_name: str,
    patient_conditions: Optional[List[str]] = None,
    current_meds: Optional[List[str]] = None,
    user_allergies: Optional[List[str]] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Evaluates safety warnings, contraindications, and drug interactions for an arbitrary medicine query.
    """
    med_clean = medicine_name.strip()
    med_lower = med_clean.lower()

    warnings: List[str] = []
    interactions_found: List[Dict[str, Any]] = []
    contraindications_found: List[str] = []
    allergy_warnings: List[str] = []
    consult_required = False

    # 1. Allergy Check
    if user_allergies:
        for allergen in user_allergies:
            if allergen.lower() in med_lower or med_lower in allergen.lower():
                msg = f"Allergy Alert: Patient has recorded allergy to '{allergen}', which matches '{med_clean}'."
                allergy_warnings.append(msg)
                warnings.append(msg)
                consult_required = True

    # 2. Contraindications Check
    conditions = [c.strip().lower() for c in (patient_conditions or []) if c]
    known_contra = KNOWLEDGE_CONTRAINDICATIONS.get(med_lower, [])

    if db:
        db_med = db.query(Medicine).filter(Medicine.medicine_name.ilike(med_clean)).first()
        if db_med and db_med.contraindications:
            known_contra = list(set(known_contra + [c.strip().lower() for c in db_med.contraindications.split(",") if c.strip()]))

    for condition in conditions:
        for contra in known_contra:
            if contra in condition or condition in contra:
                c_msg = f"Contraindication: '{med_clean}' is cautioned or contraindicated in patients with '{condition}'."
                contraindications_found.append(c_msg)
                warnings.append(c_msg)
                consult_required = True

    # 3. Drug-Drug Interactions
    meds_list = [m.strip() for m in (current_meds or []) if m.strip()]
    for other_med in meds_list:
        other_clean = other_med.lower()
        if other_clean == med_lower:
            continue

        db_inter = None
        if db:
            db_inter = db.query(MedicineInteraction).filter(
                or_(
                    (MedicineInteraction.medicine_a.ilike(med_clean)) & (MedicineInteraction.medicine_b.ilike(other_med)),
                    (MedicineInteraction.medicine_a.ilike(other_med)) & (MedicineInteraction.medicine_b.ilike(med_clean))
                )
            ).first()

        if db_inter:
            i_dict = {
                "medicine_a": db_inter.medicine_a,
                "medicine_b": db_inter.medicine_b,
                "level": db_inter.interaction_level,
                "description": db_inter.description
            }
            interactions_found.append(i_dict)
            warnings.append(f"Drug Interaction ({db_inter.interaction_level}): {med_clean} + {other_med} - {db_inter.description}")
            consult_required = True
        else:
            p1 = (med_lower, other_clean)
            p2 = (other_clean, med_lower)
            kb_inter = KNOWLEDGE_INTERACTIONS.get(p1) or KNOWLEDGE_INTERACTIONS.get(p2)
            if kb_inter:
                i_dict = {
                    "medicine_a": med_clean,
                    "medicine_b": other_med,
                    "level": kb_inter["level"],
                    "description": kb_inter["desc"]
                }
                interactions_found.append(i_dict)
                warnings.append(f"Drug Interaction ({kb_inter['level']}): {med_clean} + {other_med} - {kb_inter['desc']}")
                consult_required = True

    return {
        "medicine_name": med_clean,
        "safety_warnings": warnings,
        "interactions": interactions_found,
        "contraindications": contraindications_found,
        "allergy_warnings": allergy_warnings,
        "professional_consultation_required": consult_required
    }
