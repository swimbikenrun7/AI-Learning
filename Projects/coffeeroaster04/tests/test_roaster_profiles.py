"""Profile pages driven by the profile's roaster (rows, limits, units), using synthetic roasters."""

import unittest
from unittest import mock

import app

OWNER_EMAIL = "owner@example.com"

ROASTERS = {
    "long": {
        "name": "Long Grid C",
        "values": {
            "profile_grid_minutes": 20,
            "has_temp_readout": True,
            "temp_unit": "C",
            "temp_source": "bean_probe",
            "temp_min": 15,
            "temp_max": 300,
        },
    },
    "plain": {
        "name": "Plain F",
        "values": {
            "profile_grid_minutes": 12,
            "has_temp_readout": True,
            "temp_unit": "F",
            "temp_min": 60,
            "temp_max": 500,
        },
    },
    "dial": {
        "name": "No Readout",
        "values": {"profile_grid_minutes": 12, "has_temp_readout": False},
    },
    "calibrated": {
        "name": "Calibrated F",
        "values": {
            "profile_grid_minutes": 12,
            "has_temp_readout": True,
            "temp_unit": "F",
            "temp_min": 60,
            "temp_max": 500,
            "calibrated": True,
        },
    },
}


def blank_form(rows, **overrides):
    data = {f"temp_{minute}": "" for minute in range(1, rows + 1)}
    data.update(overrides)
    return data


class RoasterProfileTestCase(unittest.TestCase):
    def setUp(self):
        self.profiles = {}
        patchers = [
            mock.patch.object(app, "roast_profiles", self.profiles),
            mock.patch.object(app, "roasters", ROASTERS),
            mock.patch.object(app, "save_roast_profiles"),
        ]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user_email"] = OWNER_EMAIL

    def saved(self, name):
        return next(p for p in self.profiles.values() if p["name"] == name)


class TestNewProfileFollowsTheRoaster(RoasterProfileTestCase):
    def test_form_has_one_row_per_minute_of_the_roasters_grid(self):
        body = self.client.get("/profiles/new?roaster=long").get_data(as_text=True)
        self.assertIn('name="temp_20"', body)
        self.assertNotIn('name="temp_21"', body)
        body = self.client.get("/profiles/new?roaster=plain").get_data(as_text=True)
        self.assertIn('name="temp_12"', body)
        self.assertNotIn('name="temp_13"', body)

    def test_labels_use_the_roasters_unit_and_never_the_other(self):
        celsius = self.client.get("/profiles/new?roaster=long").get_data(as_text=True)
        self.assertIn("°C", celsius)
        self.assertNotIn("°F", celsius)
        fahrenheit = self.client.get("/profiles/new?roaster=plain").get_data(
            as_text=True
        )
        self.assertIn("°F", fahrenheit)
        self.assertNotIn("°C", fahrenheit)

    def test_saved_profile_has_as_many_temps_as_the_grid(self):
        data = blank_form(20, name="Twenty", roaster_id="long", temp_20="250")
        response = self.client.post("/profiles/new", data=data)
        self.assertEqual(response.status_code, 302)
        profile = self.saved("Twenty")
        self.assertEqual(len(profile["temps"]), 20)
        self.assertEqual(profile["temps"][19], 250)
        self.assertEqual(profile["roaster_id"], "long")

    def test_temperature_range_comes_from_the_roaster(self):
        ok = blank_form(20, name="In range", roaster_id="long", temp_1="299")
        self.assertEqual(self.client.post("/profiles/new", data=ok).status_code, 302)
        bad = blank_form(20, name="Too hot", roaster_id="long", temp_1="310")
        response = self.client.post("/profiles/new", data=bad)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("between 15 and 300", body)
        self.assertNotIn("Too hot", [p["name"] for p in self.profiles.values()])

    def test_target_times_cannot_exceed_the_row_count(self):
        ok = blank_form(
            12, name="At limit", roaster_id="plain", target_first_crack="12:00"
        )
        self.assertEqual(self.client.post("/profiles/new", data=ok).status_code, 302)
        bad = blank_form(
            12, name="Over", roaster_id="plain", target_first_crack="12:01"
        )
        response = self.client.post("/profiles/new", data=bad)
        self.assertEqual(response.status_code, 200)
        self.assertIn("12:00", response.get_data(as_text=True))

    def test_name_is_still_validated_before_the_roaster(self):
        response = self.client.post("/profiles/new", data=blank_form(12, name=""))
        self.assertIn("Profile name is required", response.get_data(as_text=True))


class TestRoasterWithoutAReadout(RoasterProfileTestCase):
    def test_no_temperature_grid_is_shown(self):
        body = self.client.get("/profiles/new?roaster=dial").get_data(as_text=True)
        self.assertNotIn('name="temp_1"', body)
        self.assertIn("no temperature readout", body)
        self.assertIn('name="target_first_crack"', body)  # reference times still apply

    def test_saved_profile_has_empty_temperatures(self):
        data = {
            "name": "Dial roaster",
            "roaster_id": "dial",
            "target_first_crack": "6:15",
        }
        self.assertEqual(self.client.post("/profiles/new", data=data).status_code, 302)
        profile = self.saved("Dial roaster")
        self.assertEqual(profile["temps"], [None] * 12)
        self.assertEqual(profile["target_first_crack"], 375)


class TestWizardAvailability(RoasterProfileTestCase):
    def test_wizard_is_offered_only_for_a_calibrated_roaster(self):
        for roaster_id, expected in (
            ("calibrated", True),
            ("plain", False),
            ("long", False),
            ("dial", False),
        ):
            with self.subTest(roaster=roaster_id):
                body = self.client.get(f"/profiles/new?roaster={roaster_id}").get_data(
                    as_text=True
                )
                self.assertEqual('id="wizard-toggle"' in body, expected)
                self.assertEqual("js/profile_wizard.js" in body, expected)


class TestEditingKeepsTheRoaster(RoasterProfileTestCase):
    def add_profile(self, roaster_id, temps, name="Saved"):
        self.profiles["p1"] = {
            "name": name,
            "roaster_id": roaster_id,
            "temps": temps,
            "owner": OWNER_EMAIL,
        }

    def test_a_shorter_saved_profile_is_padded_to_the_roasters_grid(self):
        self.add_profile("long", [300] + [None] * 11)
        body = self.client.get("/profiles/p1").get_data(as_text=True)
        self.assertIn('name="temp_20"', body)
        response = self.client.post(
            "/profiles/p1", data=blank_form(20, name="Saved", temp_1="300")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(self.profiles["p1"]["temps"]), 20)
        self.assertEqual(self.profiles["p1"]["temps"][0], 300)

    def test_a_longer_saved_profile_is_never_truncated(self):
        self.add_profile(
            "plain", [300] + [None] * 18 + [410]
        )  # 20 rows under a 12-row roaster
        body = self.client.get("/profiles/p1").get_data(as_text=True)
        self.assertIn('name="temp_20"', body)
        self.client.post(
            "/profiles/p1", data=blank_form(20, name="Saved", temp_20="410")
        )
        self.assertEqual(len(self.profiles["p1"]["temps"]), 20)
        self.assertEqual(self.profiles["p1"]["temps"][19], 410)

    def test_editing_never_changes_or_drops_the_roaster(self):
        self.add_profile("plain", [None] * 12)
        self.client.post("/profiles/p1", data=blank_form(12, name="Renamed"))
        self.assertEqual(self.profiles["p1"]["roaster_id"], "plain")
        self.assertEqual(self.profiles["p1"]["name"], "Renamed")

    def test_submitting_the_same_roaster_again_is_fine(self):
        self.add_profile("plain", [None] * 12)
        data = blank_form(12, name="Same", roaster_id="plain")
        self.assertEqual(self.client.post("/profiles/p1", data=data).status_code, 302)

    def test_a_profile_whose_roaster_left_the_list_still_edits_with_the_original_limits(
        self,
    ):
        self.add_profile("gone", [None] * 12)
        response = self.client.get("/profiles/p1")
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="temp_12"', response.get_data(as_text=True))
        response = self.client.post(
            "/profiles/p1", data=blank_form(12, name="Still works")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.profiles["p1"]["roaster_id"], "gone")


if __name__ == "__main__":
    unittest.main()
