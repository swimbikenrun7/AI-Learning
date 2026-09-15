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

    def test_home_offers_main_menu_buttons(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Add roast", body)
        self.assertIn("View roasts", body)
        self.assertIn("View and edit roast profiles", body)

    def test_view_roasts_lists_records(self):
        response = self.client.get("/roasts")
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


class TestListProfiles(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_lists_existing_profiles(self):
        profiles = {"profile-1": {"name": "Test Profile", "temps": [None] * 12}}
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/profiles")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Profile", response.get_data(as_text=True))

    def test_shows_message_when_no_profiles_exist(self):
        with mock.patch.object(app, "roast_profiles", {}):
            response = self.client.get("/profiles")
        self.assertEqual(response.status_code, 200)
        self.assertIn("No roast profiles exist yet", response.get_data(as_text=True))


class TestAddEditProfile(unittest.TestCase):
    def setUp(self):
        self.profiles = {
            "profile-1": {
                "name": "Existing Profile",
                "temps": [320, 365, 400] + [None] * 9,
            }
        }
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.save_patcher = mock.patch.object(app, "save_roast_profiles")
        self.profiles_patcher.start()
        self.save_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.profiles_patcher.stop()
        self.save_patcher.stop()

    def blank_temp_form(self, **overrides):
        data = {f"temp_{minute}": "" for minute in range(1, 13)}
        data.update(overrides)
        return data

    def test_new_profile_shows_blank_form(self):
        response = self.client.get("/profiles/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Add roast profile", response.get_data(as_text=True))

    def test_edit_profile_missing_returns_404(self):
        response = self.client.get("/profiles/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_edit_profile_shows_existing_values(self):
        response = self.client.get("/profiles/profile-1")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Existing Profile", body)
        self.assertIn('value="320"', body)

    def test_post_new_profile_creates_and_redirects(self):
        data = self.blank_temp_form(
            name="Brand New Profile", temp_1="300", temp_2="340", temp_3="380"
        )
        response = self.client.post("/profiles/new", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/profiles", response.headers["Location"])
        new_profiles = [
            profile
            for profile in self.profiles.values()
            if profile["name"] == "Brand New Profile"
        ]
        self.assertEqual(len(new_profiles), 1)
        self.assertEqual(new_profiles[0]["temps"][:3], [300, 340, 380])
        app.save_roast_profiles.assert_called_once_with(self.profiles)

    def test_post_new_profile_invalid_shows_error_and_preserves_input(self):
        data = self.blank_temp_form(name="", temp_1="999")
        response = self.client.post("/profiles/new", data=data)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Profile name is required", body)
        self.assertIn('value="999"', body)

    def test_post_edit_updates_existing_profile_in_place(self):
        data = self.blank_temp_form(name="Updated Name")
        response = self.client.post("/profiles/profile-1", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(set(self.profiles), {"profile-1"})
        self.assertEqual(self.profiles["profile-1"]["name"], "Updated Name")

    def test_editing_profile_does_not_alter_saved_roast_snapshot(self):
        saved_target_temps = [320, 365, 400] + [None] * 9
        roast_records = {
            "record-1": {
                "roast_profile_id": "profile-1",
                "target_temps": list(saved_target_temps),
            }
        }
        with mock.patch.object(app, "roast_records", roast_records):
            data = self.blank_temp_form(
                name="Changed Targets", **{f"temp_{m}": "999" for m in range(1, 13)}
            )
            self.client.post("/profiles/profile-1", data=data)
            self.assertEqual(
                roast_records["record-1"]["target_temps"], saved_target_temps
            )


class TestDeleteRoast(unittest.TestCase):
    def setUp(self):
        self.records = {
            "record-1": {
                "date": "09/07/2026",
                "bean_name": "Mysore Nuggets",
                "roast_profile_id": "profile-1",
                "target_temps": [320] + [None] * 11,
                "actual_temps": [320] + [None] * 11,
            }
        }
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.save_patcher = mock.patch.object(app, "save_roast_records")
        self.records_patcher.start()
        self.save_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.records_patcher.stop()
        self.save_patcher.stop()

    def test_missing_record_returns_404(self):
        response = self.client.get("/roasts/does-not-exist/delete")
        self.assertEqual(response.status_code, 404)

    def test_get_shows_confirmation(self):
        response = self.client.get("/roasts/record-1/delete")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Mysore Nuggets", body)
        self.assertIn("cannot be undone", body)
        self.assertIn("record-1", self.records)  # not deleted yet

    def test_post_deletes_record_and_redirects(self):
        response = self.client.post("/roasts/record-1/delete")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/roasts")
        self.assertNotIn("record-1", self.records)
        app.save_roast_records.assert_called_once_with(self.records)


class TestDeleteProfile(unittest.TestCase):
    def setUp(self):
        self.profiles = {"profile-1": {"name": "Test Profile", "temps": [None] * 12}}
        self.records = {
            "record-1": {
                "roast_profile_id": "profile-1",
                "target_temps": [320, 365, 400] + [None] * 9,
            }
        }
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.save_patcher = mock.patch.object(app, "save_roast_profiles")
        self.profiles_patcher.start()
        self.records_patcher.start()
        self.save_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.profiles_patcher.stop()
        self.records_patcher.stop()
        self.save_patcher.stop()

    def test_missing_profile_returns_404(self):
        response = self.client.get("/profiles/does-not-exist/delete")
        self.assertEqual(response.status_code, 404)

    def test_get_shows_confirmation_with_referencing_roast_count(self):
        response = self.client.get("/profiles/profile-1/delete")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Test Profile", body)
        self.assertIn("1 saved roast", body)
        self.assertIn("profile-1", self.profiles)  # not deleted yet

    def test_post_deletes_profile_and_redirects(self):
        response = self.client.post("/profiles/profile-1/delete")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/profiles")
        self.assertNotIn("profile-1", self.profiles)
        app.save_roast_profiles.assert_called_once_with(self.profiles)

    def test_deleting_profile_leaves_referencing_roast_snapshot_untouched(self):
        original_target_temps = list(self.records["record-1"]["target_temps"])
        self.client.post("/profiles/profile-1/delete")
        self.assertEqual(
            self.records["record-1"]["target_temps"], original_target_temps
        )
        self.assertIn("record-1", self.records)


if __name__ == "__main__":
    unittest.main()
