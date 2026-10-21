"""
Personalized Exercise & Physical Activity Recommendation Engine for HealthBridge AI
Integrates ML health-risk prediction, class vote shares, vital indicators,
recent health problems, and clinical safety contraindications based on ACSM/AHA guidelines.
"""
from typing import Dict, List, Any, Optional

def evaluate_exercise_safety(
    patient_data: dict,
    risk_level: str,
    recent_problems: List[str],
    confidence: float,
    probabilities: dict
) -> Dict[str, Any]:
    """
    Evaluates acute clinical contraindications and red-flag symptoms.
    Takes strict priority over all AI-generated exercise suggestions.
    """
    triggers = []
    chest_pain = float(patient_data.get("chest_pain_severity", 0) or 0)
    o2 = float(patient_data.get("oxygen_saturation", 98) or 98)
    hr = float(patient_data.get("heart_rate", 75) or 75)
    sbp = float(patient_data.get("systolic_blood_pressure", 120) or 120)
    
    problems_blob = " ".join(recent_problems).lower()
    
    # Red Flag 1: Active or recent chest pain/angina
    if chest_pain >= 3:
        triggers.append(f"Elevated chest pain severity ({chest_pain}/10)")
    if any(k in problems_blob for k in ["chest pain", "chest pressure", "tightness", "angina", "crushing chest", "substernal"]):
        triggers.append("Recent reported symptoms of chest discomfort, pressure, or angina")
        
    # Red Flag 2: Hypoxia or severe respiratory distress
    if o2 < 94:
        triggers.append(f"Subnormal oxygen saturation ({o2}%)")
    if any(k in problems_blob for k in ["shortness of breath", "severe breathlessness", "cannot breathe", "gasping", "dyspnea"]):
        triggers.append("Recent reported episodes of shortness of breath or dyspnea")
        
    # Red Flag 3: Syncope, fainting, or severe lightheadedness
    if any(k in problems_blob for k in ["faint", "syncope", "blackout", "passed out", "loss of consciousness", "severe dizziness", "vertigo"]):
        triggers.append("Recent history of syncope (fainting), blackouts, or severe dizziness")
        
    # Red Flag 4: Severe hemodynamic instability
    if hr >= 115:
        triggers.append(f"Resting tachycardia (Heart rate: {hr} bpm)")
    elif hr < 45:
        triggers.append(f"Resting bradycardia (Heart rate: {hr} bpm)")
        
    if sbp >= 160:
        triggers.append(f"Stage 2 hypertensive blood pressure range ({sbp} mmHg)")
    elif sbp < 90:
        triggers.append(f"Hypotensive blood pressure range ({sbp} mmHg)")
        
    # Red Flag 5: Critical Risk classification
    if "crit" in risk_level.lower():
        triggers.append("Model classification of Critical Cardiovascular Risk")

    if triggers:
        return {
            "is_exercise_cleared": False,
            "status_level": "Contraindicated_Urgent",
            "headline": "Routine Physical Exercise Contraindicated — Medical Evaluation Required",
            "safety_message": (
                "One or more warning symptoms or elevated vital markers indicate that routine, unmonitored physical exercise "
                "is currently unsafe. Physical exertion under these conditions carries significant clinical risk. "
                "Please refrain from strenuous workouts and seek immediate consultation with a qualified physician or cardiologist."
            ),
            "trigger_factors": triggers
        }

    # Cautionary / Monitored Band
    cautionary_triggers = []
    if "high" in risk_level.lower():
        cautionary_triggers.append("Elevated ML risk classification ('High Risk')")
    if sbp >= 140:
        cautionary_triggers.append(f"Borderline elevated systolic blood pressure ({sbp} mmHg)")
    if hr >= 95:
        cautionary_triggers.append(f"Elevated resting pulse ({hr} bpm)")
    if str(patient_data.get("diabetes_history", "")).strip().lower() in ["yes", "y", "true", "1"]:
        cautionary_triggers.append("Diagnosed diabetes history requiring metabolic workout monitoring")
    if int(patient_data.get("age", 40) or 40) >= 65:
        cautionary_triggers.append("Senior age group (65+) requiring gradual joint-friendly pacing")

    if cautionary_triggers:
        return {
            "is_exercise_cleared": True,
            "status_level": "Cautionary_Supervised",
            "headline": "Conservative Activity Permitted — Medical Guidance Recommended",
            "safety_message": (
                "You may engage in low-impact, gradual physical activities. Because your profile includes elevated risk indicators, "
                "we recommend obtaining formal clearance from your healthcare provider before beginning a new exercise regimen. "
                "Always adhere to a controlled pacing strategy and monitor your heart rate."
            ),
            "trigger_factors": cautionary_triggers
        }

    # Cleared / Graduated Band
    return {
        "is_exercise_cleared": True,
        "status_level": "Cleared",
        "headline": "Graduated Physical Activity Cleared — Moderate Aerobic & Mobility Focus",
        "safety_message": (
            "Your vital indicators and symptom history indicate that moderate, progressive physical activity is appropriate. "
            "Follow a balanced routine combining cardiovascular conditioning, functional mobility, and rest intervals."
        ),
        "trigger_factors": []
    }


def explain_risk_influence(
    risk_level: str,
    confidence: float,
    probabilities: dict,
    status_level: str,
    patient_data: dict,
    recent_problems: Optional[List[str]] = None
) -> str:
    """
    Transparently explains how the ML model's output and patient indicators
    informed the exercise plan, without diagnosing disease.
    Explicitly documents how recent health problems materially modified recommendations.
    """
    conf_str = f"{confidence:.1f}%"
    risk_name = risk_level.strip()
    problems_list = recent_problems or []
    
    problem_note = ""
    if problems_list:
        sample_problem = problems_list[0][:80]
        problem_note = (
            f" Contextual Symptom Modification: Our system reviewed your recorded symptom history ('{sample_problem}') "
            f"and adjusted exercise selection to eliminate high-impact orthopaedic stress or contraindicated movements."
        )
    
    if status_level == "Contraindicated_Urgent":
        return (
            f"How Your Risk Assessment Influenced This Plan: Your analysis returned a '{risk_name}' classification with a "
            f"{conf_str} model ensemble vote share. In accordance with clinical safety guidelines (ACSM/AHA), active warning "
            f"symptoms and vital thresholds override standard AI exercise suggestions. Routine workouts are withheld until "
            f"a physician can conduct a formal in-person cardiovascular examination. This precaution is designed to safeguard "
            f"your health and is not a definitive diagnosis.{problem_note}"
        )
    elif status_level == "Cautionary_Supervised":
        return (
            f"How Your Risk Assessment Influenced This Plan: Your analysis returned a '{risk_name}' classification with a "
            f"{conf_str} model ensemble vote share. Because your cardiovascular risk markers are in an intermediate-to-elevated tier, "
            f"our clinical rules selected conservative, low-impact activities (such as recumbent cycling, controlled walking, and gentle mobility) "
            f"while excluding high-intensity interval training (HIIT), heavy weightlifting, and breath-holding straining. "
            f"The model score reflects pattern similarity to clinical training clusters, rather than a definitive diagnosis of disease.{problem_note}"
        )
    else:
        return (
            f"How Your Risk Assessment Influenced This Plan: Your analysis returned a '{risk_name}' classification with a "
            f"{conf_str} model ensemble vote share. Given that your resting vitals and symptom screenings are stable, our system "
            f"prescribes a graduated aerobic building program (e.g., brisk walking, light resistance, and mobility routines) "
            f"focused on sustained cardiovascular stamina. Regular physical activity supports general wellness, but does not guarantee "
            f"specific future numerical risk reductions.{problem_note}"
        )


def generate_personalized_exercise_plan(
    patient_data: dict,
    risk_level: str,
    confidence: float,
    probabilities: dict,
    recent_problems: Optional[List[str]] = None,
    historical_medicines: Optional[List[str]] = None,
    activity_level_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for generating the complete personalized exercise recommendation.
    Tailors exercise items, guidelines, and precautions based on the intersection of:
    - ML risk category & confidence
    - Patient vitals (BP, HR, SpO2, Chest Pain)
    - Recent health problems (joint arthritis, back tension, respiratory sensitivity, etc.)
    - Medication profile (beta-blockers, anticoagulants)
    """
    problems_list = recent_problems or []
    meds_list = historical_medicines or []
    
    age = int(patient_data.get("age", 45) or 45)
    gender = str(patient_data.get("gender", "Unspecified")).strip().title()
    has_diabetes = str(patient_data.get("diabetes_history", "")).strip().lower() in ["yes", "y", "true", "1"]
    has_smoker = str(patient_data.get("smoker_status", "")).strip().lower() in ["yes", "y", "true", "1"]
    sbp = float(patient_data.get("systolic_blood_pressure", 120) or 120)
    hr = float(patient_data.get("heart_rate", 75) or 75)
    
    problems_blob = " ".join(problems_list).lower()
    
    # 1. Evaluate Safety & Contraindications
    safety_status = evaluate_exercise_safety(
        patient_data=patient_data,
        risk_level=risk_level,
        recent_problems=problems_list,
        confidence=confidence,
        probabilities=probabilities
    )
    
    status_level = safety_status["status_level"]
    is_cleared = safety_status["is_exercise_cleared"]
    
    # 2. Derive Recommendation Band
    if status_level == "Contraindicated_Urgent":
        band_name = "Restricted / Medical Evaluation First"
    elif status_level == "Cautionary_Supervised":
        band_name = "Conservative & Supervised Conditioning"
    else:
        band_name = "Graduated Moderate Aerobic Conditioning"

    # 3. Formulate Activity Level Assumption
    assumed_activity = activity_level_override or ("Sedentary / Baseline" if (age > 60 or sbp >= 140) else "Moderate Baseline")

    # 4. Formulate Transparent Explanation
    risk_influence_exp = explain_risk_influence(
        risk_level=risk_level,
        confidence=confidence,
        probabilities=probabilities,
        status_level=status_level,
        patient_data=patient_data,
        recent_problems=problems_list
    )

    exercises: List[Dict[str, Any]] = []
    general_guidelines: List[str] = []

    # Specific symptom and musculoskeletal sub-types
    has_joint_complaint = any(k in problems_blob for k in ["joint", "knee", "arthritis", "hip", "ankle", "tendonitis", "patell", "swollen joint"])
    has_back_complaint = any(k in problems_blob for k in ["back pain", "lower back", "spine", "lumbar", "posture", "stiff back", "thoracic"])
    has_respiratory_sensitivity = any(k in problems_blob for k in ["asthma", "bronchial", "seasonal breathing", "wheeze", "exercise asthma"])
    
    is_on_beta_blockers = any("metoprolol" in m.lower() or "atenolol" in m.lower() or "carvedilol" in m.lower() for m in meds_list)
    is_on_anticoagulants = any("warfarin" in m.lower() or "clopidogrel" in m.lower() or "aspirin" in m.lower() for m in meds_list)

    if not is_cleared:
        # Exercises are STRICTLY SUPPRESSED in the presence of acute warning signs
        exercises = []
        general_guidelines.extend([
            "Cease all structured cardiovascular workouts, running, resistance lifting, and sports immediately.",
            "Schedule an urgent clinical evaluation with your primary physician or cardiologist.",
            "If chest pain radiates to your arm, neck, or jaw, or if you feel dizzy or faint, call emergency services (e.g. 911 / 112) immediately.",
            "Do not attempt 'working through' pain or breathlessness under any circumstances."
        ])
    else:
        # Tailored exercises based on band and patient factors
        if "high" in risk_level.lower():
            general_guidelines.append(
                "Clinical Pre-Participation Notice: Because your assessment returned a 'High Risk' classification, formal physician clearance and exercise stress testing (e.g., treadmill ECG / CPET) are strongly advised prior to initiating any structured workout routine beyond gentle walking."
            )

        if status_level == "Cautionary_Supervised":
            # --- Intermediate / Cautionary Exercise Selection ---
            if has_joint_complaint:
                # Joint complaint: Replace weight-bearing walking with non-weight-bearing cycling and aquatic walking
                exercises.append({
                    "name": "Recumbent Stationary Cycling",
                    "category": "Low-Impact Cardiovascular",
                    "reason": "Provides aerobic conditioning with minimal knee/hip axial loading, well-suited for moderate risk with joint sensitivity.",
                    "instructions": "Adjust the seat so your knee has a slight bend at full extension. Begin with a 3-minute easy pedal warm-up at zero resistance. Maintain a steady cadence (50–60 RPM) at low resistance. Cool down for 3 minutes before dismounting.",
                    "duration": "15 to 20 minutes per session",
                    "intensity": "Light to Moderate (RPE 3–4 / 10; you should be able to speak full sentences comfortably)",
                    "frequency": "3 days per week with alternate rest days",
                    "equipment": "Recumbent exercise bicycle, supportive footwear",
                    "precautions": "Keep resistance low. Stop immediately if you experience lightheadedness, chest discomfort, or unusual pulse irregularities."
                })
                exercises.append({
                    "name": "Supervised Water Walking / Shallow Pool Mobility",
                    "category": "Aquatic Aerobic",
                    "reason": "Water buoyancy offloads up to 75% of body weight, sparing knee/hip joints while maintaining cardiovascular stimulus.",
                    "instructions": "In chest-deep water, walk forward and backward at a smooth rhythmic pace. Keep shoulders relaxed and swing arms gently through water.",
                    "duration": "15 to 20 minutes",
                    "intensity": "Light to Moderate (RPE 3 / 10)",
                    "frequency": "2 to 3 days per week",
                    "equipment": "Swimwear, non-slip aquatic water shoes",
                    "precautions": "Avoid very hot pools or saunas which can provoke sudden vasodilation. Have a pool rail or supervisor nearby."
                })
                exercises.append({
                    "name": "Gentle Seated Range-of-Motion & Dynamic Mobility",
                    "category": "Mobility & Flexibility",
                    "reason": "Maintains synovial joint lubrication and flexibility without compressive joint impact or blood pressure spikes.",
                    "instructions": "Seated in a sturdy chair: gentle ankle rolls, seated knee extensions without weights, shoulder shrugs, and controlled arm circles.",
                    "duration": "10 to 15 minutes",
                    "intensity": "Light (RPE 2 / 10)",
                    "frequency": "Daily or 5 days per week",
                    "equipment": "Sturdy armless chair",
                    "precautions": "Breathe continuously throughout each movement. Do not hold your breath."
                })
            elif has_back_complaint:
                # Back complaint: Upright walking + spinal decompression and core alignment
                exercises.append({
                    "name": "Paced Flat-Surface Walking",
                    "category": "Aerobic Conditioning",
                    "reason": "Gentle upright walking promotes nutrient exchange in intervertebral discs without high compressive loading.",
                    "instructions": "Walk on a smooth, level indoor track or flat paved surface. Maintain upright posture with gaze forward. Start with 5 minutes easy stroll, build to steady pace, end with 5 minutes stroll.",
                    "duration": "15 to 25 minutes per session",
                    "intensity": "Light to Moderate (RPE 3–4 / 10; comfortable conversational pace)",
                    "frequency": "3 to 4 days per week",
                    "equipment": "Well-cushioned athletic walking shoes, hydration bottle",
                    "precautions": "Avoid uneven trails, steep hills, or carrying heavy bags while walking."
                })
                exercises.append({
                    "name": "Spine-Spared Core Alignment & Thoracic Mobility",
                    "category": "Core & Postural Mobility",
                    "reason": "Strengthens deep lumbar stabilizers and relieves upper back tension without spinal flexion overload.",
                    "instructions": "Perform seated pelvic tilts, gentle seated thoracic rotations, and standing wall presses with a flat spine. Maintain neutral cervical spine.",
                    "duration": "10 to 15 minutes",
                    "intensity": "Light (RPE 2–3 / 10)",
                    "frequency": "4 to 5 days per week",
                    "equipment": "Sturdy chair, wall support",
                    "precautions": "Avoid loaded spinal twisting, toe touches, or standard sit-ups that compress lumbar vertebrae."
                })
                exercises.append({
                    "name": "Gentle Seated Hamstring & Hip Flexor Release",
                    "category": "Mobility & Flexibility",
                    "reason": "Alleviates pelvic posterior tilt and relieves chronic lower back tension.",
                    "instructions": "Sit on the edge of a chair with one leg extended straight ahead, heel on floor. Hinge gently forward from hips with a flat back until a light stretch is felt in the hamstring. Hold 20 seconds; switch legs.",
                    "duration": "10 minutes",
                    "intensity": "Light (RPE 2 / 10)",
                    "frequency": "Daily",
                    "equipment": "Sturdy chair",
                    "precautions": "Never round the lower back while stretching. Breathe rhythmically."
                })
            else:
                # Standard cautionary profile
                exercises.append({
                    "name": "Paced Flat-Surface Walking",
                    "category": "Aerobic Conditioning",
                    "reason": "Gradual cardiovascular stimulus with controlled elevation of myocardial oxygen demand.",
                    "instructions": "Walk on a smooth, level track or indoor surface. Start at a gentle stroll for 5 minutes. Progress to a steady, rhythmic pace where breathing is slightly elevated but comfortable. End with a 5-minute slow cooldown stroll.",
                    "duration": "15 to 25 minutes per session",
                    "intensity": "Light to Moderate (RPE 3–4 / 10; comfortable conversational pace)",
                    "frequency": "3 to 4 days per week",
                    "equipment": "Well-cushioned athletic walking shoes, hydration bottle",
                    "precautions": "Avoid steep inclines, uneven terrain, or extreme outdoor temperatures (heat/cold). Monitor heart rate regularly."
                })
                exercises.append({
                    "name": "Gentle Seated Range-of-Motion & Dynamic Mobility",
                    "category": "Mobility & Flexibility",
                    "reason": "Enhances arterial flexibility, joint mobility, and venous return without elevating systolic blood pressure.",
                    "instructions": "Perform seated ankle circles, gentle knee extensions, shoulder rolls, and seated torso rotations. Move smoothly through a comfortable range of motion. Breathe steadily throughout.",
                    "duration": "10 to 15 minutes",
                    "intensity": "Light (RPE 2 / 10)",
                    "frequency": "Daily or 5 days per week",
                    "equipment": "Sturdy armless chair",
                    "precautions": "Never hold your breath (avoid the Valsalva maneuver). Avoid rapid transitions between seated and standing."
                })
                exercises.append({
                    "name": "Supervised Water Walking / Shallow Pool Mobility",
                    "category": "Aquatic Aerobic",
                    "reason": "Buoyancy reduces joint impact by up to 75% and hydrostatic pressure supports cardiovascular circulation.",
                    "instructions": "In chest-deep water, walk forward and backward at a steady pace. Keep posture upright and swing arms gently through the water for resistance.",
                    "duration": "15 to 20 minutes",
                    "intensity": "Light to Moderate (RPE 3 / 10)",
                    "frequency": "2 days per week",
                    "equipment": "Swimwear, non-slip aquatic water shoes",
                    "precautions": "Ensure a lifeguard is on duty. Do not use very hot hydrotherapy pools or saunas, as high heat can induce acute peripheral vasodilation and hypotension."
                })

            general_guidelines.extend([
                "Perform a mandatory 5-minute warm-up before any activity and a 5-minute cool-down afterward.",
                "Never perform breath-holding (Valsalva maneuver) or heavy isometric straining, as this spikes systolic blood pressure.",
                "Use the 'Talk Test': if you cannot converse without gasping for air, slow down immediately.",
                "Consult your prescribing physician to review your exercise readiness before beginning new routines."
            ])

        else:
            # --- Cleared / Lower-Risk Exercise Selection ---
            if has_joint_complaint:
                # Lower risk with joint complaint: Low-impact joint-spared aerobic & resistance
                exercises.append({
                    "name": "Low-Impact Elliptical Gliding or Water Walking",
                    "category": "Aerobic / Cardiovascular",
                    "reason": "Delivers full aerobic conditioning while eliminating ground-strike impact forces on knee and hip cartilage.",
                    "instructions": "Begin with 5 minutes at gentle cadence and zero incline. Progress to a steady glide maintaining 55–65 RPM. Finish with a 3-minute easy cooldown glide.",
                    "duration": "20 to 30 minutes per session",
                    "intensity": "Moderate (RPE 4–5 / 10; noticeable effort, comfortably maintainable)",
                    "frequency": "3 to 4 days per week",
                    "equipment": "Elliptical trainer or access to shallow swimming pool, supportive athletic shoes",
                    "precautions": "Maintain upright posture; do not lean heavily on handrails. Avoid steep resistance ramps."
                })
                exercises.append({
                    "name": "Joint-Spared Seated Resistance & Upper Body Endurance",
                    "category": "Muscular Endurance & Metabolic Health",
                    "reason": "Improves metabolic glucose handling and lean muscle mass without deep knee flexion or axial joint compression.",
                    "instructions": "Perform 2 sets of 10–12 repetitions: Seated resistance band rows, seated chest press with bands, wall push-ups, and seated core knee lifts. Rest 60 seconds between sets.",
                    "duration": "15 to 20 minutes",
                    "intensity": "Moderate (RPE 4 / 10)",
                    "frequency": "2 to 3 non-consecutive days per week",
                    "equipment": "Light-to-medium resistance band, sturdy chair",
                    "precautions": "Avoid deep knee squats, lunges, or heavy leg press machines. Exhale on exertion."
                })
                exercises.append({
                    "name": "Non-Weight-Bearing Dynamic Flexibility",
                    "category": "Flexibility & Balance",
                    "reason": "Enhances muscular compliance and blood circulation without orthopaedic joint shear.",
                    "instructions": "Seated quad stretches, supine figure-4 hip stretches, doorway pectoral openers, and gentle ankle circles. Hold static positions 20–30 seconds.",
                    "duration": "10 to 15 minutes",
                    "intensity": "Light (RPE 2 / 10)",
                    "frequency": "Daily",
                    "equipment": "Yoga mat, sturdy chair",
                    "precautions": "Do not bounce. Stretch to mild tension, never joint pain."
                })
                exercises.append({
                    "name": "Smooth Recreational Swimming or Water Aerobics",
                    "category": "Endurance Cardiovascular",
                    "reason": "Total-body cardiovascular conditioning with zero orthopaedic shock on weight-bearing joints.",
                    "instructions": "Swim relaxed freestyle or backstroke laps with a flutter kick, alternating every 2 laps with a 30-second rest. Or perform continuous water walking drills.",
                    "duration": "20 to 25 minutes",
                    "intensity": "Moderate (RPE 4 / 10)",
                    "frequency": "2 days per week",
                    "equipment": "Swim goggles, pool access",
                    "precautions": "Stay hydrated. Avoid explosive kick turns or diving."
                })
            elif has_back_complaint:
                # Lower risk with back complaint: Upright walking + neutral spine core stabilization
                exercises.append({
                    "name": "Brisk Aerobic Walking (Paced Stride)",
                    "category": "Aerobic / Cardiovascular",
                    "reason": "Upright rhythmic movement fosters healthy lumbar disc hydration and cardiovascular conditioning.",
                    "instructions": "5-minute gentle warm-up walk, followed by 20 minutes of steady brisk walking with active arm swing. End with 5 minutes of relaxed walking.",
                    "duration": "25 to 35 minutes per session",
                    "intensity": "Moderate (RPE 4–5 / 10; noticeable effort, maintainable)",
                    "frequency": "4 to 5 days per week",
                    "equipment": "Supportive walking shoes with shock-absorbing soles",
                    "precautions": "Walk on smooth flat surfaces. Avoid carrying backpacks or uneven stride patterns."
                })
                exercises.append({
                    "name": "Neutral-Spine Core Stabilization Circuit",
                    "category": "Muscular Endurance & Spine Health",
                    "reason": "Strengthens deep abdominal and spinal erectors to create an internal muscular corset protecting the back.",
                    "instructions": "Perform 2 sets: Bird-dog holds (10 reps each side, holding 3 seconds), glute bridges (10 reps, 2-second hold), and forearm plank from knees (20–30 seconds). Rest 60 seconds between sets.",
                    "duration": "15 to 20 minutes",
                    "intensity": "Moderate (RPE 4 / 10)",
                    "frequency": "3 non-consecutive days per week",
                    "equipment": "Comfortable exercise mat",
                    "precautions": "Do not hyperextend your lower back during bird-dogs or bridges. Stop if back pain flares."
                })
                exercises.append({
                    "name": "Thoracic Spine Mobility & Postural Alignment",
                    "category": "Flexibility & Balance",
                    "reason": "Frees up thoracic spine mobility and stretches tight chest muscles that cause back tension.",
                    "instructions": "Doorway chest opening stretches, cat-cow gentle spinal mobilization on hands and knees, and chin tucks. Hold static poses for 20 seconds.",
                    "duration": "10 to 15 minutes",
                    "intensity": "Light (RPE 2 / 10)",
                    "frequency": "Daily",
                    "equipment": "Exercise mat, doorway",
                    "precautions": "Move slowly through range of motion; avoid jerky twisting."
                })
                exercises.append({
                    "name": "Low-Impact Stationary Cycling (Upright Posture)",
                    "category": "Endurance Cardiovascular",
                    "reason": "Supports cardiovascular stamina with supported spinal posture.",
                    "instructions": "Set handlebar height level with or slightly higher than the saddle to avoid forward slouching. Pedal at 60–70 RPM at moderate resistance.",
                    "duration": "20 to 25 minutes",
                    "intensity": "Moderate (RPE 4 / 10)",
                    "frequency": "2 days per week",
                    "equipment": "Upright stationary bike",
                    "precautions": "Avoid hunching or aggressively leaning forward."
                })
            else:
                # Standard lower risk profile
                exercises.append({
                    "name": "Brisk Aerobic Walking (Interval Paced)",
                    "category": "Aerobic / Cardiovascular",
                    "reason": "Strengthens cardiovascular efficiency, supports endothelial health, and promotes resting blood pressure stabilization.",
                    "instructions": "Begin with a 5-minute gentle warm-up walk. Alternate between 3 minutes of brisk walking (where breathing quickens) and 2 minutes of moderate walking. Cool down with 5 minutes of relaxed walking and light stretching.",
                    "duration": "25 to 35 minutes per session",
                    "intensity": "Moderate (RPE 4–5 / 10; noticeable effort, comfortably maintainable)",
                    "frequency": "4 to 5 days per week",
                    "equipment": "Quality running/walking shoes with arch support",
                    "precautions": "Stay well-hydrated. If outdoor temperature exceeds 30°C (86°F) or is bitterly cold, exercise indoors."
                })
                exercises.append({
                    "name": "Functional Bodyweight Resistance Circuit",
                    "category": "Muscular Endurance & Metabolic Health",
                    "reason": "Enhances insulin sensitivity, preserves lean muscle mass, and aids metabolic glucose regulation.",
                    "instructions": "Perform 2 sets of 10–12 repetitions: Chair squats (sit-to-stand), wall push-ups, standing calf raises, and seated resistance band rows. Rest 60 seconds between exercises. Exhale during exertion, inhale during recovery.",
                    "duration": "15 to 20 minutes",
                    "intensity": "Moderate (RPE 4–5 / 10)",
                    "frequency": "2 to 3 non-consecutive days per week",
                    "equipment": "Sturdy chair, light resistance band",
                    "precautions": "Avoid straining to failure. Do not hold your breath during repetitions."
                })
                exercises.append({
                    "name": "Dynamic Flexibility & Postural Alignment",
                    "category": "Flexibility & Balance",
                    "reason": "Supports musculoskeletal stability, relieves back tension, and fosters healthy circulation.",
                    "instructions": "Perform gentle hamstring stretches, chest-opening doorway stretches, cat-cow stretches, and single-leg balance holds near a wall or sturdy support. Hold static stretches for 20–30 seconds without bouncing.",
                    "duration": "10 to 15 minutes",
                    "intensity": "Light (RPE 2 / 10)",
                    "frequency": "Daily or post-workout",
                    "equipment": "Yoga mat, sturdy wall for balance support",
                    "precautions": "Stretch only to the point of gentle tension, never acute pain."
                })
                exercises.append({
                    "name": "Recreational Cycling or Swimming",
                    "category": "Endurance Cardiovascular",
                    "reason": "Low-impact full-body aerobic conditioning that minimizes repetitive orthopaedic stress.",
                    "instructions": "Cycle on flat roads or smooth bike paths at a relaxed 10–12 mph pace, or swim continuous relaxed freestyle/breaststroke laps with regular rest breaks.",
                    "duration": "20 to 30 minutes",
                    "intensity": "Moderate (RPE 4–5 / 10)",
                    "frequency": "2 days per week",
                    "equipment": "Bicycle and helmet, or swim goggles and pool access",
                    "precautions": "Wear reflective gear if cycling outdoors. Stay hydrated."
                })

            general_guidelines.extend([
                "Target a cumulative total of 150 minutes of moderate-intensity activity per week, distributed across 4 to 5 days.",
                "Include at least 2 sessions per week dedicated to major muscle group strengthening.",
                "Hydrate adequately: drink water before, during, and after physical exercise.",
                "Gradually increase duration before increasing intensity (the 'frequency-duration-intensity' progression principle)."
            ])

    # Specific clinical condition overlays
    if has_respiratory_sensitivity:
        general_guidelines.append(
            "Respiratory Sensitivity Precaution: Perform an extended 8-to-10 minute low-velocity warm-up to gradually precondition airways. Exercise in temperature-controlled indoor spaces (avoid cold, dry air), focus on nasal breathing to warm incoming airflow, and always carry your prescribed rescue inhaler."
        )
    if has_diabetes:
        general_guidelines.append(
            "Diabetes Precaution: Check your blood glucose before exercise. Carry rapid-acting carbohydrates (e.g., glucose tablets or fruit juice) in case of hypoglycemia, and inspect your feet daily for blisters or pressure spots."
        )
    if is_on_beta_blockers:
        general_guidelines.append(
            "Beta-Blocker Medication Notice: Medications such as Metoprolol lower your resting and maximum heart rate. Do not rely on target heart rate formulas (e.g. 220-age); use your perceived exertion ('Talk Test') to gauge intensity."
        )
    if is_on_anticoagulants:
        general_guidelines.append(
            "Anticoagulant Precaution: Because you take blood-thinning medications, avoid high-contact sports, rough terrain, or high-fall-risk activities to prevent traumatic bleeding."
        )

    clinical_disclaimer = (
        "Educational & Safety Notice: This personalized physical activity guidance is formulated for educational decision support "
        "based on your recorded health metrics and ACSM/AHA pre-participation screening principles. It is NOT a medical prescription or "
        "diagnostic clearance. Individuals with cardiovascular risk factors should consult their physician before starting or significantly "
        "increasing physical exercise."
    )

    return {
        "safety_status": safety_status,
        "risk_influence_explanation": risk_influence_exp,
        "activity_level_assumed": assumed_activity,
        "recommendation_band": band_name,
        "exercises": exercises,
        "general_guidelines": list(dict.fromkeys(general_guidelines)),
        "clinical_disclaimer": clinical_disclaimer
    }
