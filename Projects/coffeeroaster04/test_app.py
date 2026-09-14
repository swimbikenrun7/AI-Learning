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


class TestSelectProfile(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_lists_existing_profiles(self):
        profiles = {"profile-1": {"name": "Test Profile", "temps": [None] * 12}}
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/roasts/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Profile", response.get_data(as_text=True))

    def test_shows_message_when_no_profiles_exist(self):
        with mock.patch.object(app, "roast_profiles", {}):
            response = self.client.get("/roasts/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn("No roast profiles exist yet", response.get_data(as_text=True))


class TestAddRoast(unittest.TestCase):
    def setUp(self):
        self.records = {}
        self.profiles = {
            "profile-1": {
                "name": "Test Profile",
                "temps": [320, 365, 400, 430, 445, 455, 460] + [None] * 5,
            }
        }
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.save_patcher = mock.patch.object(app, "save_roast_records")
        self.records_patcher.start()
        self.profiles_patcher.start()
        self.save_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.records_patcher.stop()
        self.profiles_patcher.stop()
        self.save_patcher.stop()

    def valid_form_data(self):
        data = {
            "date": "09/07/2026",
            "bean_name": "Ethiopia Yirgacheffe",
            "green_weight": "205",
            "first_crack": "06:15",
            "roast_time": "07:30",
            "finished_weight": "178",
        }
        entered = [320, 365, 400, 430, 445, 455, 460] + [""] * 5
        for minute, value in enumerate(entered, start=1):
            data[f"actual_temp_{minute}"] = "" if value == "" else str(value)
        return data

    def test_missing_profile_returns_404(self):
        response = self.client.get("/roasts/new/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_get_form_shows_profile_target_temps(self):
        response = self.client.get("/roasts/new/profile-1")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Test Profile", body)
        self.assertIn("460", body)

    def test_post_valid_data_saves_record_and_redirects_to_detail(self):
        response = self.client.post(
            "/roasts/new/profile-1", data=self.valid_form_data()
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(self.records), 1)
        (record_id, record), = self.records.items()
        self.assertIn(f"/roasts/{record_id}", response.headers["Location"])
        self.assertEqual(record["bean_name"], "Ethiopia Yirgacheffe")
        self.assertEqual(record["roast_profile_id"], "profile-1")
        self.assertEqual(
            record["target_temps"], [320, 365, 400, 430, 445, 455, 460] + [460] * 5
        )
        app.save_roast_records.assert_called_once_with(self.records)

    def test_post_valid_data_redirect_shows_chart(self):
        response = self.client.post(
            "/roasts/new/profile-1", data=self.valid_form_data(), follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Ethiopia Yirgacheffe", body)
        self.assertIn("temp-chart", body)

    def test_post_invalid_field_shows_error_and_preserves_input(self):
        data = self.valid_form_data()
        data["green_weight"] = "50"  # below the 100g minimum
        response = self.client.post("/roasts/new/profile-1", data=data)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Invalid input", body)
        self.assertIn("Ethiopia Yirgacheffe", body)  # other fields preserved
        self.assertEqual(self.records, {})


if __name__ == "__main__":
    unittest.main()
