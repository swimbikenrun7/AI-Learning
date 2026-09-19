"""Add Roast, saved records, and the roast pages driven by the profile's roaster (synthetic roasters)."""

import json
import re
import unittest
from unittest import mock

import app

OWNER_EMAIL = "owner@example.com"

ROASTERS = {
    # Small-batch Celsius roaster with a 14-row grid, low floors, and no chart opening.
    "small": {
        "name": "Small C",
        "values": {
            "green_weight_min_g": 20,
            "green_weight_max_g": 60,
            "green_weight_recommended_g": 50,
            "roast_time_min_s": 180,
            "first_crack_min_s": 150,
            "profile_grid_minutes": 14,
            "has_temp_readout": True,
            "temp_unit": "C",
            "temp_source": "bean_probe",
            "temp_min": 15,
            "temp_max": 300,
        },
    },
    # A Fahrenheit roaster with the original chart opening.
    "sr": {
        "name": "SR-like F",
        "values": {
            "green_weight_min_g": 113,
            "green_weight_max_g": 227,
            "profile_grid_minutes": 12,
            "has_temp_readout": True,
            "temp_unit": "F",
            "temp_min": 60,
            "temp_max": 500,
            "chart_start_temp": 145,
            "chart_inflection_min": 0.5,
            "chart_inflection_temp": 270,
        },
    },
    "dial": {
        "name": "No Readout",
        "values": {
            "green_weight_min_g": 40,
            "green_weight_max_g": 120,
            "profile_grid_minutes": 12,
            "has_temp_readout": False,
        },
    },
}


def form(**overrides):
    data = {
        "date": "09/07/2026",
        "bean_name": "Test Bean",
        "green_weight": "50",
        "first_crack": "9:00",
        "roast_time": "12:00",
        "finished_weight": "42",
    }
    data.update(overrides)
    return data


class RoastTestCase(unittest.TestCase):
    def setUp(self):
        self.profiles = {
            "small-p": {
                "name": "Small Profile",
                "roaster_id": "small",
                "temps": [200, 230] + [None] * 12,
                "owner": OWNER_EMAIL,
            },
            "sr-p": {
                "name": "SR Profile",
                "roaster_id": "sr",
                "temps": [320, 365] + [None] * 10,
                "owner": OWNER_EMAIL,
            },
            "dial-p": {
                "name": "Dial Profile",
                "roaster_id": "dial",
                "temps": [None] * 12,
                "target_first_crack": 375,
                "owner": OWNER_EMAIL,
            },
            "legacy-p": {
                "name": "Legacy Profile",
                "temps": [320] + [None] * 11,
                "owner": OWNER_EMAIL,
            },
        }
        self.records = {}
        for patcher in (
            mock.patch.object(app, "roast_profiles", self.profiles),
            mock.patch.object(app, "roast_records", self.records),
            mock.patch.object(app, "roasters", ROASTERS),
            mock.patch.object(app, "save_roast_records"),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user_email"] = OWNER_EMAIL

    def config(self, profile_id):
        body = self.client.get(f"/roasts/new/{profile_id}").get_data(as_text=True)
        match = re.search(
            r'<script id="roast-config" type="application/json">(.*?)</script>',
            body,
            re.DOTALL,
        )
        return json.loads(match.group(1))

    def add_record(self, record_id="r1", **overrides):
        record = {
            "date": "09/07/2026",
            "bean_name": "Saved Bean",
            "green_weight": 50.0,
            "finished_weight": 42.0,
            "total_roast_time": 600,
            "time_of_first_crack": 450,
            "roast_profile_id": "small-p",
            "roaster_id": "small",
            "temp_unit": "C",
            "target_temps": [200, 230] + [None] * 12,
            "actual_temps": [201, 231] + [None] * 12,
            "owner": OWNER_EMAIL,
        }
        record.update(overrides)
        self.records[record_id] = record
        return record_id


class TestAddRoastFollowsTheRoaster(RoastTestCase):
    def test_one_row_per_profile_minute_with_the_roasters_unit(self):
        body = self.client.get("/roasts/new/small-p").get_data(as_text=True)
        self.assertIn('name="actual_temp_14"', body)
        self.assertNotIn('name="actual_temp_15"', body)
        self.assertIn("Actual (°C)", body)
        self.assertNotIn("°F", body)

    def test_limits_are_shown_as_hints(self):
        body = self.client.get("/roasts/new/small-p").get_data(as_text=True)
        self.assertIn("Allowed 20&ndash;60 g; recommended 50 g", body)
        self.assertIn("Up to 14:00", body)

    def test_a_profile_without_a_roaster_shows_no_new_hints(self):
        body = self.client.get("/roasts/new/legacy-p").get_data(as_text=True)
        self.assertNotIn("Allowed", body)
        self.assertIn("Actual (°F)", body)

    def test_batch_weight_limits_come_from_the_roaster(self):
        ok = self.client.post(
            "/roasts/new/small-p", data=form(green_weight="60", finished_weight="50")
        )
        self.assertEqual(ok.status_code, 302)
        bad = self.client.post("/roasts/new/small-p", data=form(green_weight="61"))
        self.assertEqual(bad.status_code, 200)
        self.assertIn("between 20 and 60", bad.get_data(as_text=True))

    def test_a_full_small_batch_can_finish_below_100_grams(self):
        response = self.client.post(
            "/roasts/new/sr-p", data=form(green_weight="114", finished_weight="96")
        )
        self.assertEqual(response.status_code, 302)

    def test_finished_weight_cannot_exceed_green(self):
        response = self.client.post(
            "/roasts/new/small-p", data=form(finished_weight="51")
        )
        self.assertEqual(response.status_code, 200)

    def test_roast_time_may_equal_the_row_count_but_not_exceed_it(self):
        ok = self.client.post("/roasts/new/small-p", data=form(roast_time="14:00"))
        self.assertEqual(ok.status_code, 302)
        bad = self.client.post("/roasts/new/small-p", data=form(roast_time="14:01"))
        self.assertEqual(bad.status_code, 200)
        self.assertIn("14:00", bad.get_data(as_text=True))

    def test_the_row_count_of_the_profile_not_a_fixed_20_minutes_is_the_limit(self):
        response = self.client.post(
            "/roasts/new/sr-p",
            data=form(green_weight="200", finished_weight="170", roast_time="13:00"),
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/roasts/new/legacy-p",
            data=form(green_weight="200", finished_weight="170", roast_time="13:00"),
        )
        self.assertEqual(
            response.status_code, 302
        )  # no roaster: the original 20-minute limit

    def test_a_fast_roaster_can_log_a_short_roast_and_an_early_first_crack(self):
        data = form(roast_time="3:30", first_crack="2:30")
        self.assertEqual(
            self.client.post("/roasts/new/small-p", data=data).status_code, 302
        )
        self.assertEqual(
            self.client.post(
                "/roasts/new/legacy-p",
                data=form(
                    green_weight="150",
                    finished_weight="130",
                    roast_time="3:30",
                    first_crack="2:30",
                ),
            ).status_code,
            200,
        )

    def test_actual_temperature_range_comes_from_the_roaster(self):
        ok = self.client.post("/roasts/new/small-p", data=form(actual_temp_1="300"))
        self.assertEqual(ok.status_code, 302)
        bad = self.client.post("/roasts/new/small-p", data=form(actual_temp_1="301"))
        self.assertEqual(bad.status_code, 200)

    def test_the_roaster_cannot_be_overridden_from_the_form(self):
        self.client.post(
            "/roasts/new/small-p", data=form(roaster_id="sr", temp_unit="F")
        )
        record = next(iter(self.records.values()))
        self.assertEqual(record["roaster_id"], "small")
        self.assertEqual(record["temp_unit"], "C")


class TestSavedRecordSnapshots(RoastTestCase):
    def test_record_stores_the_roaster_unit_and_full_length_lists(self):
        self.client.post(
            "/roasts/new/small-p", data=form(actual_temp_1="201", actual_temp_2="231")
        )
        record = next(iter(self.records.values()))
        self.assertEqual(record["roaster_id"], "small")
        self.assertEqual(record["temp_unit"], "C")
        self.assertEqual(len(record["target_temps"]), 14)
        self.assertEqual(len(record["actual_temps"]), 14)

    def test_a_profile_without_a_roaster_records_the_original_unit(self):
        self.client.post(
            "/roasts/new/legacy-p", data=form(green_weight="150", finished_weight="130")
        )
        record = next(iter(self.records.values()))
        self.assertIsNone(record["roaster_id"])
        self.assertEqual(record["temp_unit"], "F")
        self.assertEqual(len(record["target_temps"]), 12)


class TestRoasterWithoutAReadout(RoastTestCase):
    def test_no_temperature_entry_and_the_chart_is_hidden_but_the_timer_stays(self):
        body = self.client.get("/roasts/new/dial-p").get_data(as_text=True)
        self.assertNotIn('name="actual_temp_1"', body)
        self.assertIn('class="roast-graph" hidden', body)
        self.assertIn('id="target-temp-readout" hidden', body)
        self.assertIn('id="mark-first-crack-btn"', body)
        self.assertIn('id="start-stop-btn"', body)

    def test_a_record_saves_with_empty_temperatures_and_no_unit(self):
        response = self.client.post(
            "/roasts/new/dial-p", data=form(green_weight="100", finished_weight="85")
        )
        self.assertEqual(response.status_code, 302)
        record = next(iter(self.records.values()))
        self.assertEqual(record["actual_temps"], [None] * 12)
        self.assertIsNone(record["temp_unit"])


class TestLiveChartConfig(RoastTestCase):
    def test_units_rows_and_anchors_come_from_the_roaster(self):
        config = self.config("sr-p")
        self.assertEqual(config["rows"], 12)
        self.assertEqual(config["units"], {"symbol": "°F", "ror": "°F/min"})
        self.assertEqual(
            config["anchors"],
            {"startTemp": 145, "inflectionMin": 0.5, "inflectionTemp": 270},
        )

    def test_a_celsius_roaster_gets_celsius_and_never_the_fahrenheit_anchors(self):
        config = self.config("small-p")
        self.assertEqual(config["rows"], 14)
        self.assertEqual(config["units"], {"symbol": "°C", "ror": "°C/min"})
        self.assertIsNone(config["anchors"])

    def test_a_profile_without_a_roaster_keeps_the_original_anchors(self):
        config = self.config("legacy-p")
        self.assertEqual(config["rows"], 12)
        self.assertEqual(config["anchors"]["startTemp"], 145)

    def test_no_readout_roaster_has_no_units(self):
        self.assertIsNone(self.config("dial-p")["units"])


class TestRoastDetailFollowsTheRecord(RoastTestCase):
    def test_rows_and_unit_come_from_the_saved_record(self):
        self.add_record()
        body = self.client.get("/roasts/r1").get_data(as_text=True)
        self.assertIn("<td>14:00</td>", body)
        self.assertNotIn("<td>15:00</td>", body)
        self.assertIn("Actual (°C)", body)
        self.assertNotIn("°F", body)
        self.assertIn("Roaster: Small C", body)

    def test_the_records_own_unit_wins_over_the_roasters_current_data(self):
        self.add_record()
        changed = json.loads(json.dumps(ROASTERS))
        changed["small"]["values"]["temp_unit"] = "F"
        with mock.patch.object(app, "roasters", changed):
            body = self.client.get("/roasts/r1").get_data(as_text=True)
        self.assertIn("Actual (°C)", body)
        self.assertNotIn("°F", body)

    def test_a_record_without_a_unit_snapshot_falls_back_to_its_roasters_unit(self):
        record_id = self.add_record()
        del self.records[record_id]["temp_unit"]
        self.assertIn(
            "Actual (°C)", self.client.get("/roasts/r1").get_data(as_text=True)
        )

    def test_a_legacy_record_still_renders_in_the_original_unit_and_12_rows(self):
        record_id = self.add_record(
            green_weight=202.3,
            finished_weight=175.2,
            total_roast_time=450,
            time_of_first_crack=375,
        )
        for field in ("roaster_id", "temp_unit"):
            del self.records[record_id][field]
        self.records[record_id]["target_temps"] = [320] + [None] * 11
        self.records[record_id]["actual_temps"] = [320] + [None] * 11
        body = self.client.get("/roasts/r1").get_data(as_text=True)
        self.assertIn("Actual (°F)", body)
        self.assertIn("<td>12:00</td>", body)
        self.assertNotIn("<td>13:00</td>", body)

    def test_a_no_readout_record_shows_no_temperature_sections(self):
        self.add_record(
            roaster_id="dial",
            temp_unit=None,
            roast_profile_id="dial-p",
            target_temps=[None] * 12,
            actual_temps=[None] * 12,
        )
        response = self.client.get("/roasts/r1")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertNotIn('id="temp-chart"', body)
        self.assertIn("Weight loss", body)
        self.assertIn("Roaster: No Readout", body)

    def test_a_small_batch_record_displays_without_tripping_the_original_guards(self):
        # 50 g green / 210 s roast are valid for this roaster but outside the original limits.
        self.add_record(
            green_weight=50.0,
            finished_weight=42.0,
            total_roast_time=210,
            time_of_first_crack=150,
        )
        detail = self.client.get("/roasts/r1")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("16.00%", detail.get_data(as_text=True))
        self.assertEqual(self.client.get("/roasts").status_code, 200)
        export = self.client.get("/roasts/export")
        self.assertEqual(export.status_code, 200)
        self.assertIn("16.00", export.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
