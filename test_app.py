"""
Test suite for FitBuddy REST API endpoints and database operations.
Tests Scenarios 1, 2, and 3 along with input validation and error handling.
"""

import unittest
from fastapi.testclient import TestClient
from app import app
from database import init_db


class TestFitBuddyAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_index_page(self):
        """Test GET / returns HTML with FitBuddy branding."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("FitBuddy", res.text)
        self.assertIn("7-Day", res.text)

    def test_02_system_status(self):
        """Test GET /api/status returns database and gemini state."""
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["database_connected"])
        self.assertIn("active_model", data)

    def test_03_generate_plan_scenario_1(self):
        """Test Scenario 1: Generate 7-day personalized workout plan."""
        payload = {
            "name": "Sarah Connor",
            "age": 29,
            "weight": 64.5,
            "goal": "Weight Loss",
            "intensity": "High",
            "experience_level": "Intermediate",
            "preferences": "Dumbbells and resistance bands, 45 mins",
        }
        res = self.client.post("/generate-plan", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user_name"], "Sarah Connor")
        self.assertIsNotNone(data["plan_id"])
        self.assertIsNotNone(data["user_id"])

        days = data["plan"]["days"]
        self.assertEqual(len(days), 7)
        # Verify day structure
        day_1 = days[0]
        self.assertIn("day", day_1)
        self.assertIn("focus", day_1)
        self.assertIn("warmup", day_1)
        self.assertIn("exercises", day_1)
        self.assertIn("cooldown", day_1)
        self.assertIn("duration_minutes", day_1)

        # Store for update test
        TestFitBuddyAPI.created_user_id = data["user_id"]

    def test_04_update_plan_scenario_2(self):
        """Test Scenario 2: Update existing plan with user feedback."""
        user_id = getattr(TestFitBuddyAPI, "created_user_id", None)
        self.assertIsNotNone(user_id)

        update_payload = {
            "user_id": user_id,
            "feedback": "I have knee pain, please substitute high-impact jumps with low-impact alternatives.",
        }
        res = self.client.post("/update-plan", json=update_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_updated"])
        self.assertEqual(data["feedback"], update_payload["feedback"])
        self.assertEqual(len(data["plan"]["days"]), 7)

    def test_05_get_plan_by_user_id(self):
        """Test GET /plan/{user_id} retrieves saved plan from SQLite."""
        user_id = getattr(TestFitBuddyAPI, "created_user_id", None)
        self.assertIsNotNone(user_id)

        res = self.client.get(f"/plan/{user_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user_id"], user_id)
        self.assertEqual(len(data["plan"]["days"]), 7)

    def test_06_nutrition_tip_scenario_3(self):
        """Test Scenario 3: Request personalized nutrition & recovery tip."""
        payload = {
            "user_id": getattr(TestFitBuddyAPI, "created_user_id", None),
            "goal": "Weight Loss",
        }
        res = self.client.post("/nutrition-tip", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["goal"], "Weight Loss")
        self.assertIn("title", data)
        self.assertIn("tip", data)
        self.assertIn("hydration_tip", data)
        self.assertIn("recovery_tip", data)

    def test_07_validation_errors(self):
        """Test input validation for invalid fields."""
        # Age out of range (< 14)
        invalid_payload = {
            "name": "Kid",
            "age": 10,
            "weight": 50,
            "goal": "Muscle Gain",
            "intensity": "Medium",
            "experience_level": "Beginner",
        }
        res = self.client.post("/generate-plan", json=invalid_payload)
        self.assertEqual(res.status_code, 422)
        err = res.json()
        self.assertEqual(err["status"], "error")
        self.assertIn("14", err["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
