import unittest
from unittest import mock

import app


class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.records = {
            "record-1": {
                "date": "09/07/2026",
                "bean_name": "Mysore Nuggets",
                "green_weight": 202.3,
                "finished_weight": 175.2,
                "total_roast_time": 450,
                "time_of_first_crack": 375,
                "roast_profile_id": "profile-1",
                "target_temps": [320, 365, 400, 430, 445, 455, 460]
                + [None] * 5,
                "actual_temps": [320, 365, 400, 430, 445, 455, 460]
                + [None] * 5,
            }
        }
        self.profiles = {"profile-1": {"name": "Test Profile", "temps": [None] * 12}}
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.records_patcher.start()
        self.profiles_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.records_patcher.stop()
        self.profiles_patcher.stop()

    def test_view_roasts_lists_records(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Mysore Nuggets", body)
        self.assertIn("Test Profile", body)
        self.assertIn("City Plus", body)

    def test_roast_detail_shows_temps_and_chart(self):
        response = self.client.get("/roasts/record-1")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Mysore Nuggets", body)
        self.assertIn("Test Profile", body)
        self.assertIn("temp-chart", body)
        self.assertIn("460", body)

    def test_roast_detail_missing_record_returns_404(self):
        response = self.client.get("/roasts/does-not-exist")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
