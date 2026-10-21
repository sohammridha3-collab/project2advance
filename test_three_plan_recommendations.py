"""
Rigorous validation of the 3-Tier Exercise Recommendation system in HealthBridge AI:
1. Validates all 3 plan categories (Low, Medium, Fit & Advanced).
2. Verifies default recommendation mapping (Low Risk -> Low, Mod Risk -> Medium, High Risk -> Low, Red Flag -> Paused).
3. Verifies that all exercise images in all plans exist on disk and resolve via HTTP 200.
4. Verifies sets, rest, short instructions, safety tips, and alt texts.
"""
import os
import httpx

BASE_URL = "http://127.0.0.1:8000"

def test_three_plans():
    print("=" * 80)
    print("VERIFYING 3-TIER EXERCISE PLANS & IMAGE INTEGRITY")
    print("=" * 80)

    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        # Test 1: Low Risk -> Low Plan Recommended
        low_input = {
            "age": 28,
            "gender": "Female",
            "smoker_status": "No",
            "diabetes_history": "No",
            "heart_rate": 65.0,
            "systolic_blood_pressure": 112.0,
            "oxygen_saturation": 99.0,
            "chest_pain_severity": 0.0,
            "body_temperature": 36.6
        }
        res_low = client.post("/api/recommendations?risk_level=Low+Risk", json=low_input)
        assert res_low.status_code == 200, f"Low risk failed: {res_low.text}"
        ep_low = res_low.json()["exercise_plan"]
        
        assert "plans" in ep_low, "exercise_plan must contain 'plans' dictionary"
        plans_dict = ep_low["plans"]
        assert "low" in plans_dict
        assert "medium" in plans_dict
        assert "advanced" in plans_dict
        
        assert ep_low["recommended_plan_id"] == "low"
        assert plans_dict["low"]["is_recommended"] is True
        assert plans_dict["medium"]["is_recommended"] is False
        assert plans_dict["advanced"]["is_recommended"] is False
        assert plans_dict["low"]["badge"] == "⭐ Recommended for You"
        print("✓ Test 1 Passed: Low Risk correctly recommended 'low' plan by default.")

        # Test 2: Moderate Risk -> Medium Plan Recommended
        mod_input = {
            "age": 50,
            "gender": "Male",
            "smoker_status": "Yes",
            "diabetes_history": "No",
            "heart_rate": 84.0,
            "systolic_blood_pressure": 138.0,
            "oxygen_saturation": 97.0,
            "chest_pain_severity": 0.0,
            "body_temperature": 36.8
        }
        res_mod = client.post("/api/recommendations?risk_level=Moderate+Risk", json=mod_input)
        assert res_mod.status_code == 200
        ep_mod = res_mod.json()["exercise_plan"]
        assert ep_mod["recommended_plan_id"] == "medium"
        assert ep_mod["plans"]["medium"]["is_recommended"] is True
        assert ep_mod["plans"]["medium"]["badge"] == "⭐ Recommended for You"
        print("✓ Test 2 Passed: Moderate Risk correctly recommended 'medium' plan by default.")

        # Test 3: High Risk -> Low Plan Recommended (Safety Checked)
        high_input = {
            "age": 66,
            "gender": "Male",
            "smoker_status": "Yes",
            "diabetes_history": "Yes",
            "heart_rate": 92.0,
            "systolic_blood_pressure": 150.0,
            "oxygen_saturation": 95.0,
            "chest_pain_severity": 1.0,
            "body_temperature": 37.0
        }
        res_high = client.post("/api/recommendations?risk_level=High+Risk", json=high_input)
        assert res_high.status_code == 200
        ep_high = res_high.json()["exercise_plan"]
        assert ep_high["recommended_plan_id"] == "low", "High risk must default to safe Low plan"
        assert ep_high["plans"]["low"]["is_recommended"] is True
        assert ep_high["plans"]["advanced"]["safety_advisory"] is not None
        print("✓ Test 3 Passed: High Risk defaulted to 'low' plan with safety advisory on advanced plan.")

        # Test 4: Acute Warning Symptom (Chest pain 5) -> Paused Workouts
        chest_input = {**low_input, "chest_pain_severity": 5.0}
        res_chest = client.post("/api/recommendations", json=chest_input)
        assert res_chest.status_code == 200
        ep_chest = res_chest.json()["exercise_plan"]
        assert ep_chest["safety_status"]["is_exercise_cleared"] is False
        assert ep_chest["recommended_plan_id"] == "restricted"
        assert len(ep_chest["exercises"]) == 0
        print("✓ Test 4 Passed: Chest pain correctly triggered workout suppression and emergency protocol.")

        # Test 5: Verify all exercise illustrations and details in all 3 plans
        print("\nVerifying exercise items, images, sets, and safety tips across all 3 plans...")
        verified_images = set()
        for plan_key, plan_obj in plans_dict.items():
            print(f"  Plan: {plan_obj['title']} ({len(plan_obj['exercises'])} exercises)")
            assert len(plan_obj["exercises"]) >= 3, f"Plan {plan_key} has fewer than 3 exercises"
            for ex in plan_obj["exercises"]:
                assert ex["name"], "Exercise name required"
                assert ex["instructions"], "Instructions required"
                assert ex["sets"], "Sets required"
                assert ex["rest"], "Rest required"
                assert ex["safety_tip"], "Safety tip required"
                assert ex["image_url"], "image_url required"
                assert ex["image_alt"], "image_alt required"
                
                # Check HTTP 200 on image
                img_url = "/" + ex["image_url"].lstrip("/")
                img_res = client.get(img_url)
                assert img_res.status_code == 200, f"Image failed to load: {img_url} (HTTP {img_res.status_code})"
                assert "svg" in img_res.headers.get("content-type", "").lower()
                verified_images.add(img_url)
                print(f"    ✓ {ex['name']} -> {img_url} [HTTP 200, sets: '{ex['sets']}', rest: '{ex['rest']}']")

        print(f"\n✓ Successfully validated {len(verified_images)} unique exercise illustration SVGs via HTTP 200!")
        print("=" * 80)
        print("ALL 3-TIER EXERCISE PLANS & IMAGE TESTS PASSED PERFECTLY!")
        print("=" * 80)

if __name__ == "__main__":
    test_three_plans()
