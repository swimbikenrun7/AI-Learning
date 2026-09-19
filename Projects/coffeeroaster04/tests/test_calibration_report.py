"""The read-only calibration report (calibration_report.py), on synthetic roasters and records."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import calibration_report as report
import data_persistence

ROASTERS = {
    "cal": {
        "name": "Calibrated F",
        "values": {
            "calibrated": True,
            "temp_unit": "F",
            "wizard": {
                "time_to_first_crack_s": {"low": 375, "medium": 375, "high": 405},
                "default_first_crack_temp": 400,
                "dtr_by_level": {"Full City": 0.16, "Full City Plus": 0.18},
            },
        },
    },
    "new": {
        "name": "Uncalibrated C",
        "values": {
            "calibrated": False,
            "temp_unit": "C",
            "wizard": {
                "time_to_first_crack_s": {"low": 450, "medium": 450, "high": 450},
                "default_first_crack_temp": 200,
                "dtr_by_level": {"Full City": 0.21},
            },
        },
    },
    "dial": {
        "name": "No Readout",
        "values": {"calibrated": False, "temp_unit": None, "wizard": None},
    },
}


def record(roaster_id="cal", unit="F", **overrides):
    saved = {
        "date": "09/07/2026",
        "bean_name": "Secret Bean",
        "green_weight": 200.0,
        "finished_weight": 170.0,  # 15% loss: Full City
        "total_roast_time": 450,
        "time_of_first_crack": 375,  # development 75 s = 16.67% of the roast
        "roaster_id": roaster_id,
        "temp_unit": unit,
        "actual_temps": [300, 350, 380, 390, 395, 399, 410, 420, None, None],
        "owner": "someone@example.com",
    }
    saved.update(overrides)
    return saved


def report_for(records, roasters=ROASTERS):
    return report.build_report(
        {f"r{i}": item for i, item in enumerate(records)}, roasters, "records.json"
    )


class TestTemperatureAtFirstCrack(unittest.TestCase):
    TEMPS = (300, 350, 380, None, 395, 399)

    def test_on_a_whole_minute_it_is_that_minutes_reading(self):
        self.assertEqual(report.temperature_at_first_crack(self.TEMPS, 120), 350)

    def test_between_readings_it_is_a_straight_line(self):
        # Row 0 is the 1:00 reading (300) and row 1 the 2:00 reading (350).
        self.assertEqual(report.temperature_at_first_crack(self.TEMPS, 90), 325)
        self.assertEqual(report.temperature_at_first_crack(self.TEMPS, 105), 337.5)

    def test_a_missing_neighbouring_reading_gives_none(self):
        # The 4:00 reading is blank: the far end of 3:30, the reading itself at 4:00, the near end of 4:30.
        self.assertIsNone(report.temperature_at_first_crack(self.TEMPS, 210))
        self.assertIsNone(report.temperature_at_first_crack(self.TEMPS, 240))
        self.assertIsNone(report.temperature_at_first_crack(self.TEMPS, 270))

    def test_before_the_first_reading_or_past_the_last_gives_none(self):
        self.assertIsNone(report.temperature_at_first_crack(self.TEMPS, 45))
        self.assertIsNone(report.temperature_at_first_crack(self.TEMPS, 6 * 60 + 30))
        self.assertIsNone(report.temperature_at_first_crack(self.TEMPS, 7 * 60))

    def test_the_last_reading_is_usable_only_on_its_own_minute(self):
        self.assertEqual(report.temperature_at_first_crack(self.TEMPS, 360), 399)


class TestFormatting(unittest.TestCase):
    def test_mm_ss_rounds_to_the_second(self):
        self.assertEqual(report.format_mm_ss(375), "6:15")
        self.assertEqual(report.format_mm_ss(372.6), "6:13")
        self.assertEqual(report.format_mm_ss(5), "0:05")

    def test_signed_differences_show_their_direction(self):
        self.assertEqual(report.format_signed_mm_ss(-50), "-0:50")
        self.assertEqual(report.format_signed_mm_ss(75), "+1:15")
        self.assertEqual(report.format_signed_mm_ss(0), "+0:00")


class TestSummarize(unittest.TestCase):
    def test_it_gathers_each_roasts_numbers(self):
        summary = report.summarize(
            [record(), record(time_of_first_crack=360, finished_weight=168.0)],
            ROASTERS["cal"]["values"],
        )
        self.assertEqual(summary["first_crack"], [375, 360])
        self.assertEqual(summary["total_time"], [450, 450])
        self.assertEqual(summary["weight_loss"], [15.0, 16.0])
        self.assertEqual(
            sorted(summary["dtr_by_level"]), ["Full City", "Full City Plus"]
        )
        self.assertAlmostEqual(summary["dtr_by_level"]["Full City"][0], 75 / 450 * 100)
        self.assertAlmostEqual(
            summary["dtr_by_level"]["Full City Plus"][0], 90 / 450 * 100
        )

    def test_temperature_at_first_crack_is_read_from_the_grid(self):
        summary = report.summarize([record()], ROASTERS["cal"]["values"])
        # 6:15 lies a quarter of the way from the 6:00 reading (399) to the 7:00 reading (410).
        self.assertAlmostEqual(summary["temp_at_first_crack"][0], 399 + 11 * 0.25)

    def test_a_roast_outside_the_original_limits_is_still_summarized(self):
        # 50 g and a 3:30 roast are valid for a small roaster but outside the original guards.
        small = record(
            green_weight=50.0,
            finished_weight=42.0,
            total_roast_time=210,
            time_of_first_crack=150,
        )
        summary = report.summarize([small], ROASTERS["cal"]["values"])
        self.assertEqual(summary["weight_loss"], [16.0])
        self.assertEqual(summary["total_time"], [210])

    def test_a_reading_in_another_unit_than_the_roasters_is_left_out(self):
        summary = report.summarize([record(unit="C")], ROASTERS["cal"]["values"])
        self.assertEqual(summary["temp_at_first_crack"], [])

    def test_a_roaster_we_do_not_know_has_no_temperatures_to_compare(self):
        self.assertEqual(report.summarize([record()], {})["temp_at_first_crack"], [])

    def test_a_record_without_readings_adds_no_temperature(self):
        summary = report.summarize(
            [record("dial", None, actual_temps=[None] * 12)], ROASTERS["dial"]["values"]
        )
        self.assertEqual(summary["temp_at_first_crack"], [])


class TestReportContent(unittest.TestCase):
    def test_it_compares_with_the_roasters_stored_values(self):
        text = report_for([record(), record()])
        self.assertIn("Calibrated F: 2 roasts — calibrated", text)
        # First crack 6:15 against the stored 6:15.
        self.assertIn("median 6:15", text)
        self.assertIn("stored 6:15 (medium density, washed)   difference +0:00", text)
        # 402 °F at first crack (interpolated) against the stored 400.
        self.assertIn("median 402°F", text)
        self.assertIn("stored 400°F   difference +2°F", text)
        # Full City: 16.7% observed against 16.0% stored.
        self.assertIn("Full City", text)
        self.assertIn("observed 16.7%   stored 16.0%   difference +0.7", text)
        self.assertIn("median 15.0%", text)

    def test_first_crack_earlier_or_later_than_stored_shows_the_direction(self):
        early = report_for([record(time_of_first_crack=360)])
        self.assertIn("stored 6:15 (medium density, washed)   difference -0:15", early)
        late = report_for([record(time_of_first_crack=400)])
        self.assertIn("stored 6:15 (medium density, washed)   difference +0:25", late)

    def test_total_roast_time_is_its_own_line(self):
        text = report_for([record(total_roast_time=480), record(total_roast_time=520)])
        line = next(l for l in text.splitlines() if "Total roast time" in l)
        self.assertIn("median 8:20   range 8:00-8:40", line)

    def test_temperatures_use_the_roasters_own_unit(self):
        text = report_for([record("new", "C")])
        self.assertIn("°C", text)
        self.assertNotIn("°F", text)

    def test_a_calibrated_roaster_is_not_asked_whether_it_is_ready(self):
        text = report_for([record()])
        self.assertIn("Already calibrated", text)
        self.assertNotIn("Enough consistent data", text)

    def test_readiness_needs_enough_roasts(self):
        text = report_for([record("new", "C")] * 4)
        self.assertIn("not enough roasts yet (4 of 5)", text)

    def test_readiness_needs_consistent_first_crack_times(self):
        spread = [
            record("new", "C", time_of_first_crack=360 + 20 * n) for n in range(5)
        ]
        text = report_for(spread)  # 360 .. 440 s: 80 s apart
        self.assertIn("too spread out (1:20 apart", text)

    def test_five_consistent_roasts_are_enough_to_consider(self):
        near = [record("new", "C", time_of_first_crack=400 + 10 * n) for n in range(5)]
        self.assertIn("consider calibrating? yes", report_for(near))

    def test_first_crack_times_exactly_at_the_spread_limit_are_still_consistent(self):
        edge = [
            record("new", "C", time_of_first_crack=400 + 15 * n, total_roast_time=600)
            for n in range(5)
        ]
        self.assertIn("consider calibrating? yes", report_for(edge))  # 60 s apart

    def test_a_roaster_with_no_readout_has_no_temperature_or_stored_comparison(self):
        text = report_for([record("dial", None, actual_temps=[None] * 12)])
        self.assertIn("No Readout: 1 roast — not calibrated", text)
        self.assertNotIn("Temperature at first crack", text)
        self.assertNotIn("stored", text)
        self.assertIn("observed 16.7%", text)

    def test_a_roast_with_no_roaster_or_an_unknown_one_is_still_reported_without_comparison(
        self,
    ):
        text = report_for([record(None, "F"), record("gone", "F")])
        self.assertIn("No roaster recorded: 1 roast\n", text)
        self.assertIn("gone: 1 roast\n", text)
        self.assertNotIn("stored", text)
        self.assertNotIn("calibrated", text.split("To tune")[0])

    def test_roasters_with_more_roasts_come_first_and_ties_put_known_roasters_first(
        self,
    ):
        text = report_for(
            [record(None, "F"), record("new", "C"), record("cal"), record("cal")]
        )
        order = [
            text.index(heading)
            for heading in (
                "Calibrated F: 2",
                "Uncalibrated C: 1",
                "No roaster recorded: 1",
            )
        ]
        self.assertEqual(order, sorted(order))

    def test_no_bean_names_or_owners_appear(self):
        text = report_for([record()])
        self.assertNotIn("Secret Bean", text)
        self.assertNotIn("someone@example.com", text)

    def test_no_roasts_says_so(self):
        self.assertEqual(
            report.build_report({}, ROASTERS, "records.json"),
            "No roasts logged in records.json.",
        )

    def test_it_says_it_changes_nothing(self):
        self.assertIn("this report changes nothing", report_for([record()]))


class TestCommandLine(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.path = self.folder / "records.json"

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = report.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def write_records(self, records):
        self.path.write_text(json.dumps(records))

    def test_it_reports_on_the_named_file_using_the_real_roasters_data(self):
        self.write_records({"a": record("fresh-roast-sr800", "F")})
        code, out, _ = self.run_main("--records", str(self.path))
        self.assertEqual(code, 0)
        self.assertIn("Fresh Roast SR800: 1 roast — calibrated", out)
        self.assertIn("stored 6:15", out)

    def test_it_writes_nothing_and_leaves_the_data_path_as_it_was(self):
        self.write_records({"a": record("fresh-roast-sr800", "F")})
        before = self.path.read_bytes()
        default_path = data_persistence.ROAST_RECORDS_PATH
        self.run_main("--records", str(self.path))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual([p.name for p in self.folder.iterdir()], ["records.json"])
        self.assertEqual(data_persistence.ROAST_RECORDS_PATH, default_path)

    def test_a_missing_file_is_an_error_not_an_empty_report(self):
        code, out, err = self.run_main("--records", str(self.folder / "nope.json"))
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("no roast records file", err)

    def test_a_corrupted_file_stops_and_is_left_untouched(self):
        self.path.write_text("{not json")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as stopped:
            report.main(["--records", str(self.path)])
        self.assertEqual(stopped.exception.code, 1)
        self.assertIn("corrupted", out.getvalue())
        self.assertEqual(self.path.read_text(), "{not json")

    def test_an_empty_records_file_says_no_roasts(self):
        self.write_records({})
        code, out, _ = self.run_main("--records", str(self.path))
        self.assertEqual(code, 0)
        self.assertIn("No roasts logged", out)


if __name__ == "__main__":
    unittest.main()
