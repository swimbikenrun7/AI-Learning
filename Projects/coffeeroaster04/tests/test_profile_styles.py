"""Profile styles (drip and espresso): the helpers, migration, pages, records, and report."""

import json
import re
import unittest
from unittest import mock

import app
import calibration_report
from roasters import (
    DEFAULT_PROFILE_STYLE,
    PROFILE_STYLES,
    migrate_profile_styles,
    profile_style,
    wizard_for_style,
)
from validators import validate_profile_style

OWNER_EMAIL = "owner@example.com"
LEVELS = (
    "City Roast",
    "City Plus",
    "Full City",
    "Full City Plus",
    "Vienna Roast",
    "Italian Roast",
)
DRIP_DTR = dict(zip(LEVELS, (0.12, 0.13, 0.16, 0.18, 0.20, 0.23)))
ESPRESSO_DTR = dict(zip(LEVELS, (0.14, 0.16, 0.19, 0.22, 0.24, 0.28)))


def wizard(espresso=True):
    base = {
        "time_to_first_crack_s": {"low": 375, "medium": 375, "high": 405},
        "natural_time_adjust_s": 20,
        "dtr_by_level": DRIP_DTR,
        "profile_start_temp": 315,
        "default_first_crack_temp": 400,
    }
    if espresso:
        base["espresso"] = {
            "time_to_first_crack_s": {"low": 380, "medium": 380, "high": 410},
            "natural_time_adjust_s": 25,
            "dtr_by_level": ESPRESSO_DTR,
        }
    return base


def roaster(name, calibrated=False, with_espresso=True):
    return {
        "name": name,
        "values": {
            "profile_grid_minutes": 12,
            "has_temp_readout": True,
            "temp_unit": "F",
            "temp_min": 60,
            "temp_max": 500,
            "calibrated": calibrated,
            "wizard": wizard(with_espresso),
        },
    }


ROASTERS = {
    "cal": roaster("Calibrated F", calibrated=True),
    "plain": roaster("Plain F"),
    "drip-only": roaster("Drip Only F", with_espresso=False),
}


def wizard_config(body):
    match = re.search(
        r'<script id="wizard-config" type="application/json">(.*?)</script>',
        body,
        re.DOTALL,
    )
    return json.loads(match.group(1)) if match else None


class TestHelpers(unittest.TestCase):
    def test_a_profile_style_is_its_own_or_drip(self):
        self.assertEqual(profile_style({"style": "espresso"}), "espresso")
        self.assertEqual(profile_style({"style": "drip"}), "drip")
        for profile in ({}, None, {"style": None}, {"style": "turkish"}):
            with self.subTest(profile=profile):
                self.assertEqual(profile_style(profile), DEFAULT_PROFILE_STYLE)

    def test_the_styles_and_their_names(self):
        self.assertEqual(PROFILE_STYLES, {"drip": "Drip", "espresso": "Espresso"})
        self.assertEqual(DEFAULT_PROFILE_STYLE, "drip")

    def test_drip_uses_the_base_wizard_values_without_the_espresso_block(self):
        result = wizard_for_style(wizard(), "drip")
        self.assertEqual(result["dtr_by_level"], DRIP_DTR)
        self.assertNotIn("espresso", result)

    def test_espresso_replaces_the_style_values_and_keeps_the_machines_temperatures(
        self,
    ):
        result = wizard_for_style(wizard(), "espresso")
        self.assertEqual(result["dtr_by_level"], ESPRESSO_DTR)
        self.assertEqual(result["time_to_first_crack_s"]["medium"], 380)
        self.assertEqual(result["natural_time_adjust_s"], 25)
        self.assertEqual(result["profile_start_temp"], 315)
        self.assertEqual(result["default_first_crack_temp"], 400)
        self.assertNotIn("espresso", result)

    def test_no_espresso_values_or_no_wizard_means_none(self):
        self.assertIsNone(wizard_for_style(wizard(espresso=False), "espresso"))
        self.assertIsNone(wizard_for_style(None, "espresso"))
        self.assertIsNone(wizard_for_style(None, "drip"))

    def test_it_does_not_change_the_roasters_data(self):
        data = wizard()
        wizard_for_style(data, "espresso")
        wizard_for_style(data, "drip")
        self.assertEqual(data, wizard())

    def test_the_validator(self):
        self.assertEqual(validate_profile_style("", PROFILE_STYLES, "drip"), "drip")
        self.assertEqual(
            validate_profile_style("espresso", PROFILE_STYLES, "drip"), "espresso"
        )
        for bad in ("Espresso", "turkish", "1", " "):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_profile_style(bad, PROFILE_STYLES, "drip")


class TestMigration(unittest.TestCase):
    def test_profiles_and_records_without_a_style_become_drip(self):
        profiles = {"p1": {"name": "A"}, "p2": {"name": "B", "style": "espresso"}}
        records = {"r1": {"roast_profile_id": "p1"}, "r2": {"roast_profile_id": "gone"}}
        self.assertEqual(migrate_profile_styles(profiles, records), (True, True))
        self.assertEqual(profiles["p1"]["style"], "drip")
        self.assertEqual(profiles["p2"]["style"], "espresso")
        self.assertEqual(records["r1"]["profile_style"], "drip")
        self.assertEqual(records["r2"]["profile_style"], "drip")

    def test_a_record_takes_its_profiles_style(self):
        profiles = {"p": {"name": "A", "style": "espresso"}}
        records = {"r": {"roast_profile_id": "p"}}
        migrate_profile_styles(profiles, records)
        self.assertEqual(records["r"]["profile_style"], "espresso")

    def test_it_is_idempotent_and_reports_no_change_the_second_time(self):
        profiles = {"p": {"name": "A"}}
        records = {"r": {"roast_profile_id": "p"}}
        migrate_profile_styles(profiles, records)
        snapshot = json.dumps([profiles, records], sort_keys=True)
        self.assertEqual(migrate_profile_styles(profiles, records), (False, False))
        self.assertEqual(json.dumps([profiles, records], sort_keys=True), snapshot)

    def test_only_what_changed_is_reported(self):
        profiles = {"p": {"name": "A", "style": "drip"}}
        records = {"r": {"roast_profile_id": "p"}}
        self.assertEqual(migrate_profile_styles(profiles, records), (False, True))

    def test_an_existing_record_style_is_kept(self):
        profiles = {"p": {"name": "A", "style": "drip"}}
        records = {"r": {"roast_profile_id": "p", "profile_style": "espresso"}}
        migrate_profile_styles(profiles, records)
        self.assertEqual(records["r"]["profile_style"], "espresso")


class StyleTestCase(unittest.TestCase):
    def setUp(self):
        self.profiles = {}
        self.records = {}
        for patcher in (
            mock.patch.object(app, "roast_profiles", self.profiles),
            mock.patch.object(app, "roast_records", self.records),
            mock.patch.object(app, "roasters", ROASTERS),
            mock.patch.object(app, "save_roast_profiles"),
            mock.patch.object(app, "save_roast_records"),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user_email"] = OWNER_EMAIL

    def add_profile(self, profile_id="p", name="Profile", roaster_id="plain", **extra):
        profile = {
            "name": name,
            "roaster_id": roaster_id,
            "temps": [300] + [None] * 11,
            "owner": OWNER_EMAIL,
        }
        profile.update(extra)
        self.profiles[profile_id] = profile
        return profile_id

    def new_form(self, **overrides):
        data = {"roaster_id": "plain", "name": "Made"}
        data.update({f"temp_{minute}": "" for minute in range(1, 13)})
        data.update(overrides)
        return data


class TestChoosingAStyle(StyleTestCase):
    def test_the_chooser_offers_both_styles_with_drip_selected(self):
        body = self.client.get("/profiles/new").get_data(as_text=True)
        self.assertIn('name="style"', body)
        self.assertIn('<option value="drip" selected>Drip</option>', body)
        self.assertIn('<option value="espresso">Espresso</option>', body)

    def test_the_chosen_style_reaches_the_form(self):
        body = self.client.get("/profiles/new?roaster=plain&style=espresso").get_data(
            as_text=True
        )
        self.assertIn("Style: <strong>Espresso</strong>", body)
        self.assertIn('<input type="hidden" name="style" value="espresso">', body)

    def test_no_style_in_the_link_means_drip(self):
        body = self.client.get("/profiles/new?roaster=plain").get_data(as_text=True)
        self.assertIn("Style: <strong>Drip</strong>", body)
        self.assertIn('<input type="hidden" name="style" value="drip">', body)

    def test_an_unknown_style_goes_back_to_the_chooser_with_a_message(self):
        response = self.client.get("/profiles/new?roaster=plain&style=turkish")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Choose a profile style from the list.", body)
        self.assertIn('name="style"', body)
        self.assertNotIn('name="temp_1"', body)


class TestCreatingAndEditing(StyleTestCase):
    def test_the_style_is_saved_with_the_profile(self):
        self.client.post("/profiles/new", data=self.new_form(style="espresso"))
        self.assertEqual(next(iter(self.profiles.values()))["style"], "espresso")

    def test_a_form_without_a_style_saves_a_drip_profile(self):
        self.client.post("/profiles/new", data=self.new_form())
        self.assertEqual(next(iter(self.profiles.values()))["style"], "drip")

    def test_an_unknown_style_saves_nothing_and_says_so(self):
        response = self.client.post(
            "/profiles/new", data=self.new_form(style="turkish")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Choose a profile style from the list.", response.get_data(as_text=True)
        )
        self.assertEqual(self.profiles, {})

    def test_the_edit_form_shows_the_style_read_only(self):
        self.add_profile(style="espresso")
        body = self.client.get("/profiles/p").get_data(as_text=True)
        self.assertIn("Style: <strong>Espresso</strong>", body)
        self.assertNotIn('name="style"', body)

    def test_a_profile_saved_before_styles_existed_shows_as_drip(self):
        self.add_profile()
        self.assertIn(
            "Style: <strong>Drip</strong>",
            self.client.get("/profiles/p").get_data(as_text=True),
        )

    def test_the_style_cannot_be_changed_afterwards(self):
        self.add_profile(style="espresso")
        response = self.client.post(
            "/profiles/p", data=self.new_form(style="drip", name="Renamed")
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.profiles["p"]["name"], "Profile")
        self.assertEqual(self.profiles["p"]["style"], "espresso")

    def test_editing_without_a_style_field_keeps_the_style(self):
        self.add_profile(style="espresso")
        response = self.client.post("/profiles/p", data=self.new_form(name="Renamed"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.profiles["p"]["name"], "Renamed")
        self.assertEqual(self.profiles["p"]["style"], "espresso")


class TestTheWizardFollowsTheStyle(StyleTestCase):
    def config(self, style, roaster_id="plain"):
        body = self.client.get(
            f"/profiles/new?roaster={roaster_id}&style={style}"
        ).get_data(as_text=True)
        return wizard_config(body), body

    def test_drip_gets_the_drip_values(self):
        config, _ = self.config("drip")
        self.assertEqual(config["dtrByLevel"], DRIP_DTR)
        self.assertEqual(config["timeToFirstCrack"]["medium"], 375)

    def test_espresso_gets_the_espresso_values_and_the_same_temperatures(self):
        config, _ = self.config("espresso")
        self.assertEqual(config["dtrByLevel"], ESPRESSO_DTR)
        self.assertEqual(config["timeToFirstCrack"]["medium"], 380)
        self.assertEqual(config["naturalAdjustSeconds"], 25)
        self.assertEqual(
            (config["startTemp"], config["defaultFirstCrackTemp"]), (315, 400)
        )
        self.assertTrue(config["hasCurve"])

    def test_the_page_config_has_no_espresso_block_in_it(self):
        self.assertNotIn("espresso", self.config("drip")[0])
        self.assertNotIn("espresso", self.config("espresso")[0])

    def test_a_roaster_with_no_espresso_values_has_no_espresso_wizard(self):
        config, body = self.config("espresso", "drip-only")
        self.assertIsNone(config)
        self.assertNotIn("wizard-toggle", body)
        self.assertIsNotNone(self.config("drip", "drip-only")[0])

    def test_espresso_is_labelled_an_estimate_even_for_the_calibrated_roaster(self):
        _, espresso = self.config("espresso", "cal")
        self.assertIn("Espresso estimates", espresso)
        self.assertIn("not calibrated for any roaster", espresso)
        self.assertIn("including your Calibrated F", espresso)
        _, drip = self.config("drip", "cal")
        self.assertNotIn("Espresso estimates", drip)
        self.assertNotIn("Estimated for this roaster", drip)

    def test_an_uncalibrated_roasters_espresso_shows_both_notices(self):
        _, body = self.config("espresso", "plain")
        self.assertIn("Espresso estimates", body)
        self.assertIn("Estimated for this roaster", body)
        self.assertNotIn("including your", body)


class TestShowingTheStyle(StyleTestCase):
    def test_the_profile_list_tags_each_profile_with_its_style(self):
        self.add_profile("a", "Espresso one", style="espresso")
        self.add_profile("b", "Drip one", style="drip")
        self.add_profile("c", "Old one")
        body = self.client.get("/profiles").get_data(as_text=True)
        self.assertEqual(body.count('class="style-tag"'), 3)
        self.assertIn('<span class="style-tag">&middot; Espresso</span>', body)
        self.assertEqual(body.count('<span class="style-tag">&middot; Drip</span>'), 2)

    def test_the_profile_picker_and_add_roast_heading_show_it(self):
        self.add_profile(style="espresso")
        picker = self.client.get("/roasts/new").get_data(as_text=True)
        self.assertIn('<span class="style-tag">&middot; Espresso</span>', picker)
        heading = self.client.get("/roasts/new/p").get_data(as_text=True)
        self.assertIn('<span class="style-tag">&middot; Espresso</span></h1>', heading)

    def test_the_roaster_tag_is_untouched(self):
        self.add_profile(style="espresso")
        body = self.client.get("/profiles").get_data(as_text=True)
        self.assertEqual(body.count('class="roaster-tag"'), 1)
        self.assertIn('<span class="roaster-tag">&middot; Plain F</span>', body)


class TestRecordsSnapshotTheStyle(StyleTestCase):
    def post_roast(self, profile_id):
        return self.client.post(
            f"/roasts/new/{profile_id}",
            data={
                "date": "09/07/2026",
                "bean_name": "Bean",
                "green_weight": "150",
                "first_crack": "6:15",
                "roast_time": "8:00",
                "finished_weight": "128",
            },
        )

    def test_a_saved_roast_records_its_profiles_style(self):
        self.add_profile(style="espresso")
        self.post_roast("p")
        self.assertEqual(next(iter(self.records.values()))["profile_style"], "espresso")

    def test_a_profile_without_a_style_records_drip(self):
        self.add_profile()
        self.post_roast("p")
        self.assertEqual(next(iter(self.records.values()))["profile_style"], "drip")

    def test_the_style_stays_on_the_record_if_the_profile_is_edited_or_deleted(self):
        self.add_profile(style="espresso")
        self.post_roast("p")
        del self.profiles["p"]
        record_id = next(iter(self.records))
        body = self.client.get(f"/roasts/{record_id}").get_data(as_text=True)
        self.assertIn("Style: Espresso", body)

    def test_the_detail_page_shows_the_style_and_old_records_show_drip(self):
        base = {
            "date": "09/07/2026",
            "bean_name": "Bean",
            "green_weight": 150.0,
            "finished_weight": 128.0,
            "total_roast_time": 480,
            "time_of_first_crack": 375,
            "roaster_id": "plain",
            "temp_unit": "F",
            "target_temps": [None] * 12,
            "actual_temps": [None] * 12,
            "owner": OWNER_EMAIL,
        }
        self.records["espresso-record"] = {**base, "profile_style": "espresso"}
        self.records["old-record"] = dict(base)
        espresso = self.client.get("/roasts/espresso-record").get_data(as_text=True)
        old = self.client.get("/roasts/old-record").get_data(as_text=True)
        self.assertIn("Style: Espresso", espresso)
        self.assertIn("Style: Drip", old)


def logged_roast(style=None, first_crack=375, total=450, finished=170.0):
    record = {
        "date": "09/07/2026",
        "bean_name": "Bean",
        "green_weight": 200.0,
        "finished_weight": finished,  # 15% loss: Full City
        "total_roast_time": total,
        "time_of_first_crack": first_crack,
        "roaster_id": "cal",
        "temp_unit": "F",
        "actual_temps": [None] * 12,
        "owner": OWNER_EMAIL,
    }
    if style:
        record["profile_style"] = style
    return record


class TestCalibrationReportKeepsStylesApart(unittest.TestCase):
    def report(self, records):
        return calibration_report.build_report(
            {f"r{i}": record for i, record in enumerate(records)},
            ROASTERS,
            "records.json",
        )

    def test_drip_and_espresso_roasts_get_separate_sections(self):
        text = self.report([logged_roast(), logged_roast("espresso")])
        self.assertIn("Calibrated F: 1 roast — calibrated", text)
        self.assertIn("Calibrated F (Espresso): 1 roast — not calibrated", text)

    def test_espresso_is_compared_with_the_espresso_values(self):
        # 75 s of development in 450 s is 16.7%: 0.7 above drip Full City (16%) and
        # 2.3 below espresso Full City (19%).
        text = self.report([logged_roast("espresso")])
        self.assertIn("observed 16.7%   stored 19.0%   difference -2.3", text)
        self.assertIn("stored 6:20", text)  # the espresso first-crack time, 380 s
        drip = self.report([logged_roast()])
        self.assertIn("observed 16.7%   stored 16.0%   difference +0.7", drip)
        self.assertIn("stored 6:15", drip)

    def test_espresso_is_never_calibrated_even_on_the_calibrated_roaster(self):
        text = self.report([logged_roast("espresso")])
        self.assertNotIn("Already calibrated", text)
        self.assertIn("consider calibrating?", text)

    def test_a_record_with_no_style_is_drip(self):
        text = self.report([logged_roast(), logged_roast(None)])
        self.assertIn("Calibrated F: 2 roasts — calibrated", text)
        self.assertNotIn("Espresso", text)

    def test_a_roaster_with_no_espresso_values_gets_no_stored_comparison(self):
        record = {**logged_roast("espresso"), "roaster_id": "drip-only"}
        text = self.report([record])
        self.assertIn("Drip Only F (Espresso): 1 roast", text)
        self.assertNotIn("stored", text)


if __name__ == "__main__":
    unittest.main()
