"""
Personalized Exercise & Physical Activity Recommendation Engine for HealthBridge AI
Provides three distinct exercise tiers (Low, Medium, Fit & Advanced),
connects to patient vitals, ML risk outputs, and recent symptoms,
and applies clinical safety contraindications in simple, easy-to-understand English.
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
    Evaluates acute clinical warning symptoms and red-flag vitals.
    Safety warnings take priority over routine workouts.
    """
    triggers = []
    chest_pain = float(patient_data.get("chest_pain_severity", 0) or 0)
    o2 = float(patient_data.get("oxygen_saturation", 98) or 98)
    hr = float(patient_data.get("heart_rate", 75) or 75)
    sbp = float(patient_data.get("systolic_blood_pressure", 120) or 120)
    
    problems_blob = " ".join(recent_problems).lower()
    
    # Red Flag 1: Active chest pain
    if chest_pain >= 3:
        triggers.append(f"Chest discomfort score of {chest_pain}/10")
    if any(k in problems_blob for k in ["chest pain", "chest pressure", "tightness", "angina", "crushing chest", "substernal"]):
        triggers.append("Recent symptoms of chest pain or tight chest pressure")
        
    # Red Flag 2: Low oxygen or severe shortness of breath
    if o2 < 94:
        triggers.append(f"Low blood oxygen level ({o2}%)")
    if any(k in problems_blob for k in ["shortness of breath", "severe breathlessness", "cannot breathe", "gasping", "dyspnea"]):
        triggers.append("Recent severe shortness of breath")
        
    # Red Flag 3: Fainting or blackouts
    if any(k in problems_blob for k in ["faint", "syncope", "blackout", "passed out", "loss of consciousness", "severe dizziness", "vertigo"]):
        triggers.append("Recent episode of fainting, blackout, or severe dizziness")
        
    # Red Flag 4: Unstable heart rate or blood pressure
    if hr >= 115:
        triggers.append(f"Fast resting heart rate ({hr} bpm)")
    elif hr < 45:
        triggers.append(f"Very slow resting heart rate ({hr} bpm)")
        
    if sbp >= 160:
        triggers.append(f"High blood pressure reading ({sbp} mmHg)")
    elif sbp < 90:
        triggers.append(f"Very low blood pressure reading ({sbp} mmHg)")
        
    # Red Flag 5: Critical Risk classification
    if "crit" in risk_level.lower():
        triggers.append("Critical risk category result")

    if triggers:
        return {
            "is_exercise_cleared": False,
            "status_level": "Contraindicated_Urgent",
            "headline": "Workouts Paused - Please Seek Medical Advice",
            "safety_message": (
                "Because you have one or more warning signs (such as chest discomfort, low oxygen, or fainting), "
                "routine physical workouts are paused right now. Exercising under these conditions can be unsafe. "
                "Please rest and check with a doctor or health clinic before starting any exercise."
            ),
            "trigger_factors": triggers
        }

    # Cautionary Band
    cautionary_triggers = []
    if "high" in risk_level.lower():
        cautionary_triggers.append("Higher cardiovascular risk score")
    if sbp >= 140:
        cautionary_triggers.append(f"Borderline elevated blood pressure ({sbp} mmHg)")
    if hr >= 95:
        cautionary_triggers.append(f"Elevated resting pulse ({hr} bpm)")
    if str(patient_data.get("diabetes_history", "")).strip().lower() in ["yes", "y", "true", "1"]:
        cautionary_triggers.append("Diabetes history (requires glucose check before workouts)")
    if int(patient_data.get("age", 40) or 40) >= 65:
        cautionary_triggers.append("Age 65+ (benefits from smooth, gentle pacing)")

    if cautionary_triggers:
        return {
            "is_exercise_cleared": True,
            "status_level": "Cautionary_Supervised",
            "headline": "Light & Moderate Activity Permitted - Take It Easy",
            "safety_message": (
                "You can safely do gentle, low-impact exercise. Because some of your numbers are elevated, "
                "we suggest starting slowly and speaking with your doctor before trying challenging workouts. "
                "Always stop and rest if you feel dizzy or tired."
            ),
            "trigger_factors": cautionary_triggers
        }

    # Cleared Band
    return {
        "is_exercise_cleared": True,
        "status_level": "Cleared",
        "headline": "Regular Activity Cleared - Ready to Move",
        "safety_message": (
            "Your vital signs and health history look stable. You can choose any of the three plans below. "
            "Start with the recommended plan and move up as your stamina grows."
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
    Transparently explains how the risk result and health history guided the plan,
    using simple, friendly English.
    """
    conf_str = f"{confidence:.1f}%"
    risk_name = risk_level.strip()
    problems_list = recent_problems or []
    
    problem_note = ""
    if problems_list:
        sample_problem = problems_list[0][:60]
        problem_note = f" We also noticed your recent record of '{sample_problem}', so we swapped out high-impact moves for joint-friendly alternatives."

    if status_level == "Contraindicated_Urgent":
        return (
            f"Why workouts are paused: Your analysis showed '{risk_name}' with a {conf_str} model score. "
            f"Because active warning signs were detected, all routine exercises are paused until a doctor checks your heart and vitals in person.{problem_note}"
        )
    elif status_level == "Cautionary_Supervised":
        if "high" in risk_level.lower():
            return (
                f"How your result guided this plan: Your assessment returned '{risk_name}' ({conf_str} confidence). "
                f"We recommend starting with the Low Exercise Plan (light walking and gentle stretches). Avoid heavy lifting until cleared by your doctor.{problem_note}"
            )
        else:
            return (
                f"How your result guided this plan: Your assessment returned '{risk_name}' ({conf_str} confidence). "
                f"A balanced routine of brisk walking, wall push-ups, and light bands is recommended to build healthy stamina safely.{problem_note}"
            )
    else:
        return (
            f"How your result guided this plan: Your assessment returned '{risk_name}' ({conf_str} confidence) with stable vital signs. "
            f"The Low Exercise Plan is highlighted as an easy starting point, but you can freely explore the Medium or Fit & Advanced plans as you feel ready.{problem_note}"
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
    Main generator for the 3 distinct exercise plans:
    - Low Exercise Plan
    - Medium Exercise Plan
    - Fit & Advanced Plan
    Personalizes exercises, images, instructions, and safety tips based on patient data.
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
    
    # 1. Safety assessment
    safety_status = evaluate_exercise_safety(
        patient_data=patient_data,
        risk_level=risk_level,
        recent_problems=problems_list,
        confidence=confidence,
        probabilities=probabilities
    )
    status_level = safety_status["status_level"]
    is_cleared = safety_status["is_exercise_cleared"]
    
    # Check specific symptom conditions
    has_joint_complaint = any(k in problems_blob for k in ["joint", "knee", "arthritis", "hip", "ankle", "tendonitis", "patell", "swollen joint"])
    has_back_complaint = any(k in problems_blob for k in ["back pain", "lower back", "spine", "lumbar", "posture", "stiff back", "thoracic"])
    has_respiratory_sensitivity = any(k in problems_blob for k in ["asthma", "bronchial", "seasonal breathing", "wheeze", "exercise asthma"])
    is_on_beta_blockers = any("metoprolol" in m.lower() or "atenolol" in m.lower() or "carvedilol" in m.lower() for m in meds_list)
    is_on_anticoagulants = any("warfarin" in m.lower() or "clopidogrel" in m.lower() or "aspirin" in m.lower() for m in meds_list)

    # 2. Formulate 3 distinct exercise lists
    
    # ==========================
    # PLAN A: LOW EXERCISE PLAN
    # ==========================
    low_exercises: List[Dict[str, Any]] = []
    
    if has_joint_complaint:
        low_exercises.append({
            "name": "Recumbent Stationary Cycling",
            "category": "Light Aerobic",
            "reason": "Pedaling in a seated bucket chair keeps your knees and hips cushioned with zero ground impact.",
            "instructions": "Adjust the seat so your knees have a slight bend. Pedal smoothly at low resistance for 15 minutes.",
            "duration": "15 to 20 minutes",
            "intensity": "Light (RPE 2-3 / 10)",
            "frequency": "3 to 4 days a week",
            "equipment": "Stationary exercise bike",
            "precautions": "Keep resistance very light. Stop if your knees ache.",
            "image_url": "assets/exercises/recumbent_cycling.svg",
            "image_alt": "Person cycling on a recumbent stationary bike",
            "sets": "1 session",
            "rest": "Rest as needed",
            "safety_tip": "Do not push heavy gears; keep pedal motion smooth and easy."
        })
    else:
        low_exercises.append({
            "name": "Easy Paced Walking",
            "category": "Light Aerobic",
            "reason": "A calm, steady walk warms up your muscles and gently increases blood circulation.",
            "instructions": "Walk on flat ground at a relaxed, comfortable stride. You should easily be able to talk without losing your breath.",
            "duration": "15 to 20 minutes",
            "intensity": "Light (RPE 2-3 / 10)",
            "frequency": "4 to 5 days a week",
            "equipment": "Comfortable walking shoes",
            "precautions": "Choose flat pavements or indoor tracks. Avoid steep hills.",
            "image_url": "assets/exercises/easy_walking.svg",
            "image_alt": "Person walking calmly on a level path",
            "sets": "1 continuous walk",
            "rest": "Take short 1-minute pauses if needed",
            "safety_tip": "Wear supportive shoes and stop if your feet or calves feel sore."
        })

    low_exercises.append({
        "name": "Gentle Standing & Shoulder Stretch",
        "category": "Flexibility",
        "reason": "Releases shoulder tightness and improves chest expansion without any strain.",
        "instructions": "Stand tall, roll your shoulders back gently, and reach both arms toward the ceiling. Hold for 20 seconds while breathing slowly.",
        "duration": "5 to 10 minutes",
        "intensity": "Very Light (RPE 1-2 / 10)",
        "frequency": "Daily",
        "equipment": "None",
        "precautions": "Stretch only until you feel a pleasant pull. Never bounce or force a stretch.",
        "image_url": "assets/exercises/gentle_stretching.svg",
        "image_alt": "Person doing gentle standing stretch with arms raised",
        "sets": "3 rounds",
        "rest": "20 seconds rest between stretches",
        "safety_tip": "Keep your breathing slow and steady throughout each stretch."
    })

    low_exercises.append({
        "name": "Chair Sit-to-Stand",
        "category": "Beginner Bodyweight",
        "reason": "Builds leg and hip strength using a chair, making everyday standing easier.",
        "instructions": "Sit upright in a sturdy chair with feet flat. Lean slightly forward, stand up smoothly, then sit back down under control.",
        "duration": "5 to 8 minutes",
        "intensity": "Light (RPE 3 / 10)",
        "frequency": "3 days a week",
        "equipment": "Sturdy dining or office chair",
        "precautions": "Avoid rocking backwards. Place your hands on chair armrests if you need extra support.",
        "image_url": "assets/exercises/chair_sit_stand.svg",
        "image_alt": "Person standing up smoothly from a sturdy chair",
        "sets": "2 sets of 8 to 10 repetitions",
        "rest": "60 seconds rest between sets",
        "safety_tip": "Press through your heels and keep your knees pointing forward."
    })

    low_exercises.append({
        "name": "Deep Breathing & Neck Mobility",
        "category": "Breathing & Mobility",
        "reason": "Calms the nervous system, lowers tension, and gently relaxes your neck muscles.",
        "instructions": "Sit upright. Inhale deeply through your nose for 4 seconds, then exhale slowly through your mouth. Gently turn your head left and right.",
        "duration": "5 minutes",
        "intensity": "Very Light (RPE 1 / 10)",
        "frequency": "Daily or before bed",
        "equipment": "Comfortable chair",
        "precautions": "Never roll your head all the way back. Stop if you feel lightheaded.",
        "image_url": "assets/exercises/deep_breathing.svg",
        "image_alt": "Person seated comfortably doing relaxed deep breathing",
        "sets": "1 session",
        "rest": "Continuous relaxed breathing",
        "safety_tip": "Focus on relaxed, full exhales to help lower resting blood pressure."
    })

    # ==========================
    # PLAN B: MEDIUM EXERCISE PLAN
    # ==========================
    medium_exercises: List[Dict[str, Any]] = []

    if has_joint_complaint:
        medium_exercises.append({
            "name": "Pool Water Walking",
            "category": "Moderate Aerobic",
            "reason": "Water takes 75% of your weight off your knees while water resistance gives a great workout.",
            "instructions": "Walk forward and backward in chest-deep water at a steady clip. Swing your arms naturally through the water.",
            "duration": "20 to 25 minutes",
            "intensity": "Moderate (RPE 4 / 10)",
            "frequency": "3 days a week",
            "equipment": "Swimwear and pool access",
            "precautions": "Ensure a lifeguard is present. Avoid hot tubs or saunas.",
            "image_url": "assets/exercises/water_walking.svg",
            "image_alt": "Person walking briskly in chest-deep swimming pool",
            "sets": "1 session",
            "rest": "Pause for 30 seconds every 5 minutes",
            "safety_tip": "Step gently on the pool floor and maintain upright posture."
        })
    else:
        medium_exercises.append({
            "name": "Brisk Interval Walking",
            "category": "Moderate Aerobic",
            "reason": "Walking with short energetic bursts strengthens your heart muscle and burns calories.",
            "instructions": "Warm up for 3 minutes. Alternate 3 minutes of fast walking with 2 minutes of relaxed walking for 20 minutes.",
            "duration": "20 to 25 minutes",
            "intensity": "Moderate (RPE 4-5 / 10)",
            "frequency": "4 days a week",
            "equipment": "Running or walking sneakers",
            "precautions": "Slow down immediately if you cannot talk in short sentences.",
            "image_url": "assets/exercises/brisk_walking.svg",
            "image_alt": "Person power-walking briskly with active arm swing",
            "sets": "4 to 5 intervals",
            "rest": "3 minutes relaxed cooldown stroll",
            "safety_tip": "Take the 'Talk Test' - you should be able to speak short sentences."
        })

    medium_exercises.append({
        "name": "Wall Push-Ups",
        "category": "Bodyweight Strength",
        "reason": "Strengthens your chest, shoulders, and arms without floor strain or wrist pain.",
        "instructions": "Stand arm's length from a sturdy wall. Place hands flat, bend your elbows to bring your chest close to the wall, then push back.",
        "duration": "5 to 8 minutes",
        "intensity": "Moderate (RPE 4 / 10)",
        "frequency": "3 days a week",
        "equipment": "Clear wall space",
        "precautions": "Do not sag your hips or arch your lower back.",
        "image_url": "assets/exercises/wall_pushups.svg",
        "image_alt": "Person performing controlled push-ups against a wall",
        "sets": "2 to 3 sets of 10 to 12 reps",
        "rest": "45 seconds rest between sets",
        "safety_tip": "Breathe out as you push away from the wall; breathe in as you lower."
    })

    medium_exercises.append({
        "name": "Bodyweight / Chair Squats",
        "category": "Leg Strength",
        "reason": "Firms thigh and glute muscles, improving balance and knee support.",
        "instructions": "Stand with feet shoulder-width apart. Lower your hips back as if sitting down, keeping knees behind toes, then press up.",
        "duration": "8 minutes",
        "intensity": "Moderate (RPE 4-5 / 10)",
        "frequency": "3 days a week",
        "equipment": "Optional chair for safety",
        "precautions": "Stop if your knees feel sharp pain. Only squat as low as comfortable.",
        "image_url": "assets/exercises/bodyweight_squats.svg",
        "image_alt": "Person performing a controlled bodyweight half-squat",
        "sets": "2 sets of 10 to 12 reps",
        "rest": "60 seconds rest between sets",
        "safety_tip": "Keep your chest up and do not let your knees cave inward."
    })

    medium_exercises.append({
        "name": "Resistance Band Pulls",
        "category": "Resistance Training",
        "reason": "Builds upper back strength, straightens posture, and relieves desk neck tension.",
        "instructions": "Hold an elastic band out in front with both hands. Pull your hands outward across your chest, squeezing shoulder blades together.",
        "duration": "8 minutes",
        "intensity": "Moderate (RPE 4 / 10)",
        "frequency": "3 days a week",
        "equipment": "Light resistance band",
        "precautions": "Do not let the band snap back; control the return slowly.",
        "image_url": "assets/exercises/resistance_band.svg",
        "image_alt": "Person stretching resistance band horizontally across chest",
        "sets": "2 sets of 12 reps",
        "rest": "45 seconds rest between sets",
        "safety_tip": "Keep your shoulders down away from your ears."
    })

    medium_exercises.append({
        "name": "Glute Bridge & Core Hold",
        "category": "Core & Lower Back",
        "reason": "Stabilizes the pelvis and supports the lower spine without any sit-up strain.",
        "instructions": "Lie on your back with knees bent and feet flat. Squeeze your hips upward toward the ceiling, hold for 2 seconds, and lower slowly.",
        "duration": "6 to 8 minutes",
        "intensity": "Moderate (RPE 3-4 / 10)",
        "frequency": "3 days a week",
        "equipment": "Yoga mat or soft carpet",
        "precautions": "Do not over-arch your lower back at the top.",
        "image_url": "assets/exercises/glute_bridge.svg",
        "image_alt": "Person lying on mat with hips lifted in a bridge pose",
        "sets": "2 sets of 10 reps",
        "rest": "45 seconds rest between sets",
        "safety_tip": "Keep your core lightly tightened throughout each repetition."
    })

    # ==========================
    # PLAN C: FIT & ADVANCED PLAN
    # ==========================
    advanced_exercises: List[Dict[str, Any]] = []

    advanced_exercises.append({
        "name": "Fast-Paced Cardio / Cycling",
        "category": "Cardio Endurance",
        "reason": "Elevates aerobic capacity, boosts heart rate safely, and enhances stamina.",
        "instructions": "Warm up for 3 minutes. Pedal at 65-75 RPM at moderate resistance, or jog at a solid, brisk rhythm.",
        "duration": "25 to 30 minutes",
        "intensity": "Moderately Vigorous (RPE 6 / 10)",
        "frequency": "3 to 4 days a week",
        "equipment": "Stationary bike, outdoor bicycle, or running shoes",
        "precautions": "Stay hydrated. Slow down if your breathing turns into panting.",
        "image_url": "assets/exercises/tempo_cycling.svg",
        "image_alt": "Person cycling briskly on stationary trainer",
        "sets": "1 continuous session",
        "rest": "5 minutes easy cooldown",
        "safety_tip": "Sip water every 10 minutes and monitor your heart rate."
    })

    advanced_exercises.append({
        "name": "Floor or Incline Push-Ups",
        "category": "Progressive Strength",
        "reason": "Strengthens upper body pressing power, triceps, and abdominal core.",
        "instructions": "Start in a straight plank with hands slightly wider than shoulders. Lower your chest until almost touching the mat, then press up.",
        "duration": "8 to 10 minutes",
        "intensity": "Vigorous (RPE 6 / 10)",
        "frequency": "3 days a week",
        "equipment": "Exercise mat (or sturdy bench for incline)",
        "precautions": "Never drop your lower back. Drop to knees if form breaks.",
        "image_url": "assets/exercises/floor_pushups.svg",
        "image_alt": "Person in horizontal plank push-up position on mat",
        "sets": "3 sets of 10 to 15 reps",
        "rest": "60 seconds rest between sets",
        "safety_tip": "Breathe out forcefully as you push up; avoid holding your breath."
    })

    advanced_exercises.append({
        "name": "Dumbbell / Band Strength Circuit",
        "category": "Progressive Strength",
        "reason": "Builds upper arm, back, and shoulder muscle tone with controlled weights.",
        "instructions": "Hold light dumbbells (3 to 8 lbs) or a firm band. Perform bicep curls followed by gentle overhead presses in a smooth tempo.",
        "duration": "10 to 12 minutes",
        "intensity": "Moderate to Vigorous (RPE 5-6 / 10)",
        "frequency": "3 days a week",
        "equipment": "Light dumbbells (3-8 lbs) or loop band",
        "precautions": "Do not swing your body or arch your back to lift the weight.",
        "image_url": "assets/exercises/dumbbell_curls.svg",
        "image_alt": "Person standing with dumbbells curling weights with good form",
        "sets": "3 sets of 10 to 12 reps",
        "rest": "60 seconds rest between sets",
        "safety_tip": "Use a weight you can control smoothly through the entire motion."
    })

    advanced_exercises.append({
        "name": "Supported Step Lunges",
        "category": "Lower Body Power",
        "reason": "Develops single-leg balance, quad strength, and strong hip stabilizers.",
        "instructions": "Step forward with your right leg and bend both knees to 90 degrees. Press firmly off your front foot to return to standing.",
        "duration": "8 to 10 minutes",
        "intensity": "Moderate to Vigorous (RPE 5-6 / 10)",
        "frequency": "3 days a week",
        "equipment": "Sturdy wall or chair for balance support",
        "precautions": "Keep front knee above your ankle. Do not let front knee slide past toes.",
        "image_url": "assets/exercises/step_lunges.svg",
        "image_alt": "Person in balanced stepping forward lunge pose",
        "sets": "2 to 3 sets of 8 to 10 reps per leg",
        "rest": "60 seconds rest between sets",
        "safety_tip": "Hold a wall for balance until your leg coordination feels solid."
    })

    advanced_exercises.append({
        "name": "Forearm Plank Hold",
        "category": "Core Stability",
        "reason": "Strengthens deep abdominal wall, shoulders, and spine without bending your back.",
        "instructions": "Rest on forearms and toes (or knees for an easier version). Hold your body in a straight line while breathing rhythmically.",
        "duration": "5 minutes",
        "intensity": "Moderate to Vigorous (RPE 6 / 10)",
        "frequency": "3 to 4 days a week",
        "equipment": "Yoga mat",
        "precautions": "Do not let your hips sink down or pike up into a triangle.",
        "image_url": "assets/exercises/plank_hold.svg",
        "image_alt": "Person holding clean straight forearm plank on mat",
        "sets": "3 holds of 20 to 30 seconds each",
        "rest": "45 seconds rest between holds",
        "safety_tip": "Breathe continuously; stop immediately if your lower back aches."
    })

    # 3. Determine recommended plan based on latest risk & vitals
    if not is_cleared:
        recommended_plan_id = "restricted"
        recommended_plan_title = "Workouts Paused (Medical Check Required)"
        recommended_reason = (
            "Because your assessment showed warning signs (such as chest discomfort, low oxygen, or fainting), "
            "exercise plans are temporarily paused. Please speak with a doctor before resuming exercise."
        )
        plan_low = {
            "id": "low",
            "title": "Low Exercise Plan",
            "tagline": "Gentle daily movements without weights or strain",
            "target_audience": "Best for light activity, seniors, or recovery days",
            "is_recommended": False,
            "badge": None,
            "why_recommended": "Currently on hold due to reported symptoms.",
            "safety_advisory": "Routine workouts are on hold until checked by a doctor.",
            "exercises": []
        }
        plan_medium = {
            "id": "medium",
            "title": "Medium Exercise Plan",
            "tagline": "Balanced moderate workout for stamina and strength",
            "target_audience": "Best for active individuals wanting steady cardio",
            "is_recommended": False,
            "badge": None,
            "why_recommended": "Currently on hold due to reported symptoms.",
            "safety_advisory": "Routine workouts are on hold until checked by a doctor.",
            "exercises": []
        }
        plan_advanced = {
            "id": "advanced",
            "title": "Fit & Advanced Plan",
            "tagline": "Challenging workout for fitness and muscle tone",
            "target_audience": "Best for individuals cleared for higher fitness",
            "is_recommended": False,
            "badge": None,
            "why_recommended": "Currently on hold due to reported symptoms.",
            "safety_advisory": "Routine workouts are on hold until checked by a doctor.",
            "exercises": []
        }
    elif "high" in risk_level.lower() or status_level == "Cautionary_Supervised" and sbp >= 145:
        # High Risk: Recommend Low Plan by default with cautious advisories
        recommended_plan_id = "low"
        recommended_plan_title = "Low Exercise Plan"
        recommended_reason = (
            "Your health assessment shows higher cardiovascular risk. We recommend starting with light walking "
            "and gentle stretches. Please talk with your doctor before attempting moderate or higher-intensity workouts."
        )
        plan_low = {
            "id": "low",
            "title": "Low Exercise Plan",
            "tagline": "Gentle daily movements without weights or strain",
            "target_audience": "Best for light activity, seniors, or recovery days",
            "is_recommended": True,
            "badge": "⭐ Recommended for You",
            "why_recommended": "Recommended for your current risk level to keep your heart and joints safe.",
            "safety_advisory": None,
            "exercises": low_exercises
        }
        plan_medium = {
            "id": "medium",
            "title": "Medium Exercise Plan",
            "tagline": "Balanced moderate workout for stamina and strength",
            "target_audience": "Best for active individuals wanting steady cardio",
            "is_recommended": False,
            "badge": None,
            "why_recommended": "A step up once your doctor approves moderate workouts.",
            "safety_advisory": "Caution: Your risk is elevated. Please consult your physician before trying moderate workouts.",
            "exercises": medium_exercises
        }
        plan_advanced = {
            "id": "advanced",
            "title": "Fit & Advanced Plan",
            "tagline": "Challenging workout for fitness and muscle tone",
            "target_audience": "Best for individuals cleared for higher fitness",
            "is_recommended": False,
            "badge": None,
            "why_recommended": "Not currently advised without personal physician clearance.",
            "safety_advisory": "Important: High-intensity workouts are not advised for your current risk tier.",
            "exercises": advanced_exercises
        }
    elif "mod" in risk_level.lower():
        # Moderate Risk: Recommend Medium Plan by default
        recommended_plan_id = "medium"
        recommended_plan_title = "Medium Exercise Plan"
        recommended_reason = (
            "Your risk result is Moderate. A balanced routine of brisk walking, chair squats, and light bands "
            "will help improve your cardiovascular stamina safely."
        )
        plan_low = {
            "id": "low",
            "title": "Low Exercise Plan",
            "tagline": "Gentle daily movements without weights or strain",
            "target_audience": "Best for light activity, seniors, or recovery days",
            "is_recommended": False,
            "badge": None,
            "why_recommended": "Great for recovery days or when you want an easier session.",
            "safety_advisory": None,
            "exercises": low_exercises
        }
        plan_medium = {
            "id": "medium",
            "title": "Medium Exercise Plan",
            "tagline": "Balanced moderate workout for stamina and strength",
            "target_audience": "Best for active individuals wanting steady cardio",
            "is_recommended": True,
            "badge": "⭐ Recommended for You",
            "why_recommended": "Matches your Moderate Risk result: builds stamina with safe, steady pacing.",
            "safety_advisory": None,
            "exercises": medium_exercises
        }
        plan_advanced = {
            "id": "advanced",
            "title": "Fit & Advanced Plan",
            "tagline": "Challenging workout for fitness and muscle tone",
            "target_audience": "Best for individuals cleared for higher fitness",
            "is_recommended": False,
            "badge": None,
            "why_recommended": "Take it slow if trying these exercises; stop if breathing gets ragged.",
            "safety_advisory": "Notice: This plan is more demanding. Take extra rest breaks if you try it.",
            "exercises": advanced_exercises
        }
    else:
        # Low Risk: Recommend Low Plan as default foundation, but all 3 are fully open!
        recommended_plan_id = "low"
        recommended_plan_title = "Low Exercise Plan"
        recommended_reason = (
            "Your vital signs are healthy and in the Low Risk category. This gentle plan is a great daily foundation. "
            "You can also freely choose the Medium or Fit & Advanced plans whenever you want more challenge!"
        )
        plan_low = {
            "id": "low",
            "title": "Low Exercise Plan",
            "tagline": "Gentle daily movements without weights or strain",
            "target_audience": "Best for light activity, seniors, or recovery days",
            "is_recommended": True,
            "badge": "⭐ Recommended for You",
            "why_recommended": "A gentle, sustainable daily routine to keep your heart healthy.",
            "safety_advisory": None,
            "exercises": low_exercises
        }
        plan_medium = {
            "id": "medium",
            "title": "Medium Exercise Plan",
            "tagline": "Balanced moderate workout for stamina and strength",
            "target_audience": "Best for active individuals wanting steady cardio",
            "is_recommended": False,
            "badge": None,
            "why_recommended": "Perfect when you want a slightly more energetic workout.",
            "safety_advisory": None,
            "exercises": medium_exercises
        }
        plan_advanced = {
            "id": "advanced",
            "title": "Fit & Advanced Plan",
            "tagline": "Challenging workout for fitness and muscle tone",
            "target_audience": "Best for individuals cleared for higher fitness",
            "is_recommended": False,
            "badge": None,
            "why_recommended": "Great for high-energy days when you want to build strength.",
            "safety_advisory": None,
            "exercises": advanced_exercises
        }

    plans = {
        "low": plan_low,
        "medium": plan_medium,
        "advanced": plan_advanced
    }

    # Backward compatibility: exercises top-level array
    active_exercises = plans[recommended_plan_id]["exercises"] if recommended_plan_id in plans else []

    # 4. Formulate General Guidelines in short, simple English
    guidelines = [
        "Drink water before, during, and after your workout.",
        "Warm up for 3 to 5 minutes before exercising, and cool down with an easy stroll afterward.",
        "Take the 'Talk Test' - if you cannot converse without gasping, slow down immediately.",
        "Rest on days when you feel unusually tired, sore, or unwell."
    ]

    if has_diabetes:
        guidelines.append("Diabetes Tip: Check your blood sugar before workouts and keep a fruit juice or glucose snack nearby.")
    if is_on_beta_blockers:
        guidelines.append("Heart Medicine Notice: Your medicine keeps your heart rate low. Measure your effort by how you feel, not by a fitness watch.")
    if is_on_anticoagulants:
        guidelines.append("Safety Note: Because you take blood-thinning medicine, choose low-fall-risk exercises on flat, even ground.")
    if has_respiratory_sensitivity:
        guidelines.append("Breathing Tip: Exercise indoors in a comfortable room. Keep your inhaler handy and take a warm-up stroll.")
    if "high" in risk_level.lower():
        guidelines.append("High Risk Advisory: Schedule a clinical pre-participation review with your doctor before trying challenging workouts.")

    explanation = explain_risk_influence(
        risk_level=risk_level,
        confidence=confidence,
        probabilities=probabilities,
        status_level=status_level,
        patient_data=patient_data,
        recent_problems=problems_list
    )

    disclaimer = (
        "Educational Notice: This exercise plan is for general wellness guidance. It is not a medical prescription. "
        "Always check with your doctor before starting a new workout routine, especially if you have heart or health concerns."
    )

    return {
        "safety_status": safety_status,
        "risk_influence_explanation": explanation,
        "activity_level_assumed": activity_level_override or ("Sedentary / Baseline" if (age > 60 or sbp >= 140) else "Moderate Baseline"),
        "recommendation_band": recommended_plan_title,
        "recommended_plan_id": recommended_plan_id,
        "recommended_plan_title": recommended_plan_title,
        "recommended_reason": recommended_reason,
        "plans": plans,
        "exercises": active_exercises,
        "general_guidelines": list(dict.fromkeys(guidelines)),
        "clinical_disclaimer": disclaimer
    }
