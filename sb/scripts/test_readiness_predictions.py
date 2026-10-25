"""
Comprehensive Test Suite for AI-Nomad Travel Readiness ML Predictor.

Validates the 9 mandatory evaluation scenarios:
1. Fully prepared traveler
2. Missing visa when visa is required
3. Missing passport/documents
4. Flight and hotel not booked
5. Packing incomplete
6. High weather risk
7. Poor overall preparation
8. Invalid input
9. Missing model file
"""

import os
import sys
import unittest

# Add script directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from predict_readiness import predict_readiness, load_readiness_model, validate_readiness_input


class TestReadinessPredictions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensure the model is trained and available."""
        load_readiness_model()

    def test_1_fully_prepared_traveler(self):
        """Scenario 1: Fully prepared traveler should achieve a top score (95-100)."""
        data = {
            "destination_country": "Japan",
            "trip_duration_days": 10,
            "season": "Spring",
            "previous_trips": 5,
            "flight_booked": 1,
            "hotel_booked": 1,
            "passport_valid": 1,
            "visa_required": 1,
            "visa_ready": 1,
            "documents_completed": 1,
            "travel_insurance": 1,
            "emergency_prepared": 1,
            "country_preparation": 1,
            "packing_completed": 1,
            "weather_risk": "LOW",
        }
        res = predict_readiness(data)
        print("\n[Test 1] Fully Prepared Traveler:", res)
        self.assertGreaterEqual(res["preparedness_score"], 95)
        self.assertEqual(res["readiness_band"], "Departure Ready")
        self.assertTrue(any("valid" in f.lower() or "visa" in f.lower() for f in res["top_factors"]))

    def test_2_missing_visa_when_required(self):
        """Scenario 2: Missing visa when required must severely cap readiness (<= 48)."""
        data = {
            "destination_country": "United States",
            "trip_duration_days": 14,
            "season": "Summer",
            "previous_trips": 3,
            "flight_booked": 1,
            "hotel_booked": 1,
            "passport_valid": 1,
            "visa_required": 1,
            "visa_ready": 0,  # Missing mandatory visa
            "documents_completed": 1,
            "travel_insurance": 1,
            "emergency_prepared": 1,
            "country_preparation": 1,
            "packing_completed": 1,
            "weather_risk": "LOW",
        }
        res = predict_readiness(data)
        print("\n[Test 2] Missing Visa When Required:", res)
        self.assertLessEqual(res["preparedness_score"], 48)
        self.assertIn(res["readiness_band"], ["Critical Risk", "Moderate Readiness"])
        self.assertTrue(any("visa" in f.lower() and "not" in f.lower() for f in res["top_factors"]))

    def test_3_missing_passport_documents(self):
        """Scenario 3: Missing passport or invalid documents must trigger a critical cap (<= 42)."""
        data = {
            "destination_country": "France",
            "trip_duration_days": 7,
            "season": "Autumn",
            "previous_trips": 2,
            "flight_booked": 1,
            "hotel_booked": 1,
            "passport_valid": 0,  # Invalid passport
            "visa_required": 0,
            "visa_ready": 1,
            "documents_completed": 0,
            "travel_insurance": 1,
            "emergency_prepared": 1,
            "country_preparation": 1,
            "packing_completed": 1,
            "weather_risk": "LOW",
        }
        res = predict_readiness(data)
        print("\n[Test 3] Missing Passport / Documents:", res)
        self.assertLessEqual(res["preparedness_score"], 42)
        self.assertEqual(res["readiness_band"], "Critical Risk")
        self.assertTrue(any("passport" in f.lower() for f in res["top_factors"]))

    def test_4_flight_and_hotel_not_booked(self):
        """Scenario 4: Missing both flight and hotel bookings should noticeably reduce score."""
        baseline = {
            "destination_country": "Italy",
            "trip_duration_days": 8,
            "season": "Summer",
            "previous_trips": 4,
            "flight_booked": 1,
            "hotel_booked": 1,
            "passport_valid": 1,
            "visa_required": 0,
            "visa_ready": 1,
            "documents_completed": 1,
            "travel_insurance": 1,
            "emergency_prepared": 1,
            "country_preparation": 1,
            "packing_completed": 1,
            "weather_risk": "LOW",
        }
        unbooked = {**baseline, "flight_booked": 0, "hotel_booked": 0}

        res_base = predict_readiness(baseline)
        res_unbooked = predict_readiness(unbooked)
        print(f"\n[Test 4] Booked ({res_base['preparedness_score']}) vs Unbooked ({res_unbooked['preparedness_score']}):", res_unbooked)
        self.assertGreater(res_base["preparedness_score"], res_unbooked["preparedness_score"] + 15)
        self.assertTrue(any("flight" in f.lower() and "not" in f.lower() for f in res_unbooked["top_factors"]))

    def test_5_packing_incomplete(self):
        """Scenario 5: Incomplete packing should reduce score and be flagged in top factors."""
        packed = {
            "destination_country": "Greece",
            "trip_duration_days": 6,
            "season": "Summer",
            "previous_trips": 2,
            "flight_booked": 1,
            "hotel_booked": 1,
            "passport_valid": 1,
            "visa_required": 0,
            "visa_ready": 1,
            "documents_completed": 1,
            "travel_insurance": 1,
            "emergency_prepared": 1,
            "country_preparation": 1,
            "packing_completed": 1,
            "weather_risk": "LOW",
        }
        unpacked = {**packed, "packing_completed": 0}

        res_packed = predict_readiness(packed)
        res_unpacked = predict_readiness(unpacked)
        print(f"\n[Test 5] Packed ({res_packed['preparedness_score']}) vs Incomplete Packing ({res_unpacked['preparedness_score']}):", res_unpacked)
        self.assertGreater(res_packed["preparedness_score"], res_unpacked["preparedness_score"] + 10)
        self.assertTrue(any("packing is incomplete" in f.lower() for f in res_unpacked["top_factors"]))

    def test_6_high_weather_risk(self):
        """Scenario 6: High weather risk combined with incomplete packing penalizes readiness."""
        low_risk = {
            "destination_country": "Thailand",
            "trip_duration_days": 10,
            "season": "Summer",
            "previous_trips": 1,
            "flight_booked": 1,
            "hotel_booked": 1,
            "passport_valid": 1,
            "visa_required": 0,
            "visa_ready": 1,
            "documents_completed": 1,
            "travel_insurance": 1,
            "emergency_prepared": 0,
            "country_preparation": 1,
            "packing_completed": 0,
            "weather_risk": "LOW",
        }
        high_risk = {**low_risk, "weather_risk": "HIGH"}

        res_low = predict_readiness(low_risk)
        res_high = predict_readiness(high_risk)
        print(f"\n[Test 6] Weather Low Risk ({res_low['preparedness_score']}) vs High Risk ({res_high['preparedness_score']}):", res_high)
        self.assertGreater(res_low["preparedness_score"], res_high["preparedness_score"])
        self.assertTrue(any("weather" in f.lower() for f in res_high["top_factors"]))

    def test_7_poor_overall_preparation(self):
        """Scenario 7: Traveler with almost no preparation should score very low (< 25)."""
        data = {
            "destination_country": "India",
            "trip_duration_days": 21,
            "season": "Winter",
            "previous_trips": 0,
            "flight_booked": 0,
            "hotel_booked": 0,
            "passport_valid": 0,
            "visa_required": 1,
            "visa_ready": 0,
            "documents_completed": 0,
            "travel_insurance": 0,
            "emergency_prepared": 0,
            "country_preparation": 0,
            "packing_completed": 0,
            "weather_risk": "HIGH",
        }
        res = predict_readiness(data)
        print("\n[Test 7] Poor Overall Preparation:", res)
        self.assertLessEqual(res["preparedness_score"], 25)
        self.assertEqual(res["readiness_band"], "Critical Risk")

    def test_8_invalid_input(self):
        """Scenario 8: Invalid inputs must raise ValueError with descriptive feedback."""
        # Missing fields
        with self.assertRaises(ValueError) as ctx:
            validate_readiness_input({"destination_country": "Japan"})
        self.assertIn("Missing required fields", str(ctx.exception))

        # Invalid season
        with self.assertRaises(ValueError) as ctx:
            validate_readiness_input({
                "destination_country": "Japan",
                "trip_duration_days": 5,
                "season": "Monsoon_Season",
                "previous_trips": 0,
                "flight_booked": 1,
                "hotel_booked": 1,
                "passport_valid": 1,
                "visa_required": 0,
                "visa_ready": 1,
                "documents_completed": 1,
                "travel_insurance": 1,
                "emergency_prepared": 1,
                "country_preparation": 1,
                "packing_completed": 1,
                "weather_risk": "LOW",
            })
        self.assertIn("Invalid season", str(ctx.exception))

        # Negative duration
        with self.assertRaises(ValueError) as ctx:
            validate_readiness_input({
                "destination_country": "Japan",
                "trip_duration_days": -4,
                "season": "Spring",
                "previous_trips": 0,
                "flight_booked": 1,
                "hotel_booked": 1,
                "passport_valid": 1,
                "visa_required": 0,
                "visa_ready": 1,
                "documents_completed": 1,
                "travel_insurance": 1,
                "emergency_prepared": 1,
                "country_preparation": 1,
                "packing_completed": 1,
                "weather_risk": "LOW",
            })
        self.assertIn("trip_duration_days", str(ctx.exception))
        print("\n[Test 8] Invalid Inputs correctly caught with descriptive ValueErrors.")

    def test_9_missing_model_file(self):
        """Scenario 9: Non-existent model path must raise FileNotFoundError with actionable message."""
        fake_path = "/tmp/non_existent_readiness_model_12345.pkl"
        with self.assertRaises(FileNotFoundError) as ctx:
            load_readiness_model(fake_path)
        self.assertIn("Run sb/scripts/train_readiness_model.py first", str(ctx.exception))
        print("\n[Test 9] Missing Model File correctly raises FileNotFoundError.")


if __name__ == "__main__":
    print("=" * 65)
    print("RUNNING TRAVEL READINESS ML PREDICTOR TEST SUITE")
    print("=" * 65)
    unittest.main(verbosity=2)
