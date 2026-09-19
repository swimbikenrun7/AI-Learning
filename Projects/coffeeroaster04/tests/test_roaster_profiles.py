"""Profile pages driven by the profile's roaster (rows, limits, units), using synthetic roasters."""

import json
import re
import unittest
from unittest import mock

import app
from data_persistence import load_roasters

OWNER_EMAIL = "owner@example.com"

DTR = {
    "City Roast": 0.16,
    "City Plus": 0.18,
    "Full City": 0.21,
    "Full City Plus": 0.24,
    "Vienna Roast": 0.27,
    "Italian Roast": 0.31,
}


def wizard(start_temp=None, first_crack_temp=None, natural=None):
    return {
        "time_to_first_crack_s": {"low": 400, "medium": 400, "high": 430},
        "natural_time_adjust_s": natural,
        "dtr_by_level": DTR,
        "profile_start_temp": start_temp,
        "default_first_crack_temp": first_crack_temp,
    }


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
            "wizard": wizard(),  # times only: no temperatures to build a curve from
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
            "wizard": wizard(start_temp=315, first_crack_temp=400, natural=20),
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


def wizard_config(body):
    match = re.search(
        r'<script id="wizard-config" type="application/json">(.*?)</script>',
        body,
        re.DOTALL,
    )
    return json.loads(match.group(1)) if match else None


class TestWizardFollowsTheRoaster(RoasterProfileTestCase):
    def new_profile_page(self, roaster_id):
        return self.client.get(f"/profiles/new?roaster={roaster_id}").get_data(
            as_text=True
        )

    def test_wizard_is_offered_wherever_the_roaster_has_wizard_data(self):
        for roaster_id, expected in (
            ("calibrated", True),
            ("long", True),  # not calibrated, but it has (times-only) wizard data
            ("plain", False),  # no wizard data
            ("dial", False),  # no readout
        ):
            with self.subTest(roaster=roaster_id):
                body = self.new_profile_page(roaster_id)
                self.assertEqual('id="wizard-toggle"' in body, expected)
                self.assertEqual("js/profile_wizard.js" in body, expected)
                self.assertEqual(wizard_config(body) is not None, expected)

    def test_an_uncalibrated_roaster_gets_the_estimate_notice_and_a_calibrated_one_does_not(
        self,
    ):
        self.assertIn("Estimated for this roaster", self.new_profile_page("long"))
        self.assertIn(
            "Long Grid C these are starting estimates", self.new_profile_page("long")
        )
        self.assertNotIn(
            "Estimated for this roaster", self.new_profile_page("calibrated")
        )

    def test_the_temperature_field_and_curve_only_appear_when_a_curve_is_possible(self):
        curve = self.new_profile_page("calibrated")
        self.assertIn('id="wizard-fc-temp" value="400" min="60" max="500"', curve)
        self.assertIn("a starting curve and target times", curve)
        self.assertNotIn("No temperature curve for this roaster", curve)
        times_only = self.new_profile_page("long")
        self.assertNotIn('id="wizard-fc-temp"', times_only)
        self.assertIn("No temperature curve for this roaster", times_only)
        self.assertIn("the target first-crack and development times below", times_only)

    def test_config_carries_the_roasters_own_numbers(self):
        config = wizard_config(self.new_profile_page("calibrated"))
        self.assertEqual(config["rows"], 12)
        self.assertEqual(
            config["timeToFirstCrack"], {"low": 400, "medium": 400, "high": 430}
        )
        self.assertEqual(config["naturalAdjustSeconds"], 20)
        self.assertEqual(config["dtrByLevel"], DTR)
        self.assertEqual(config["startTemp"], 315)
        self.assertEqual(config["defaultFirstCrackTemp"], 400)
        self.assertTrue(config["hasCurve"])

    def test_times_only_config_and_an_unknown_natural_adjustment(self):
        config = wizard_config(self.new_profile_page("long"))
        self.assertEqual(config["rows"], 20)
        self.assertFalse(config["hasCurve"])
        self.assertIsNone(config["startTemp"])
        self.assertEqual(
            config["naturalAdjustSeconds"], 0
        )  # unknown means no adjustment

    def test_the_curve_needs_both_temperatures(self):
        for start, first_crack in ((315, None), (None, 400)):
            with self.subTest(start=start, first_crack=first_crack):
                roasters = json.loads(json.dumps(ROASTERS))
                roasters["calibrated"]["values"]["wizard"] = wizard(start, first_crack)
                with mock.patch.object(app, "roasters", roasters):
                    config = wizard_config(self.new_profile_page("calibrated"))
                self.assertFalse(config["hasCurve"])

    def test_the_edit_page_has_no_wizard(self):
        self.profiles["p1"] = {
            "name": "Saved",
            "roaster_id": "calibrated",
            "temps": [None] * 12,
            "owner": OWNER_EMAIL,
        }
        body = self.client.get("/profiles/p1").get_data(as_text=True)
        self.assertNotIn('id="wizard-toggle"', body)
        self.assertIsNone(wizard_config(body))


class TestWizardWithTheRealRoasterData(RoasterProfileTestCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(app, "roasters", load_roasters())
        patcher.start()
        self.addCleanup(patcher.stop)

    def config(self, roaster_id):
        body = self.client.get(f"/profiles/new?roaster={roaster_id}").get_data(
            as_text=True
        )
        return wizard_config(body), body

    def test_sr800_config_is_exactly_its_data_and_has_no_notice(self):
        config, body = self.config("fresh-roast-sr800")
        self.assertEqual(config["rows"], 12)
        self.assertEqual(
            config["timeToFirstCrack"], {"low": 375, "medium": 375, "high": 405}
        )
        self.assertEqual(config["naturalAdjustSeconds"], 20)
        self.assertEqual(config["dtrByLevel"]["Full City"], 0.16)
        self.assertEqual(
            (config["startTemp"], config["defaultFirstCrackTemp"]), (315, 400)
        )
        self.assertTrue(config["hasCurve"])
        self.assertNotIn("Estimated for this roaster", body)

    def test_the_other_sr_models_get_a_curve_with_the_estimate_notice(self):
        for roaster_id in ("fresh-roast-sr540", "fresh-roast-sr700"):
            with self.subTest(roaster=roaster_id):
                config, body = self.config(roaster_id)
                self.assertTrue(config["hasCurve"])
                self.assertIn("Estimated for this roaster", body)

    def test_roasters_without_start_temperatures_get_times_only(self):
        for roaster_id in (
            "kaffelogic-nano-7",
            "hottop-kn-8828b-2k",
            "quest-m3",
            "gene-cafe-cbr-101",
        ):
            with self.subTest(roaster=roaster_id):
                config, body = self.config(roaster_id)
                self.assertFalse(config["hasCurve"])
                self.assertIn("Estimated for this roaster", body)
                self.assertNotIn('id="wizard-fc-temp"', body)

    def test_a_long_grid_reaches_the_wizard_and_gene_cafes_natural_adjustment_is_negative(
        self,
    ):
        config, _ = self.config("gene-cafe-cbr-101")
        self.assertEqual(config["rows"], 25)
        self.assertEqual(config["naturalAdjustSeconds"], -30)

    def test_no_readout_roasters_have_no_wizard(self):
        for roaster_id in (
            "whirley-pop-stovetop-popcorn-popper",
            "fresh-roast-sr300",
            "nesco-cr-1010-pr",
        ):
            with self.subTest(roaster=roaster_id):
                config, body = self.config(roaster_id)
                self.assertIsNone(config)
                self.assertNotIn('id="wizard-toggle"', body)


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
