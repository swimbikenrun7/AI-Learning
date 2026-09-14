import tempfile
import unittest
from pathlib import Path
from unittest import mock

import data_persistence
from calculations import (
    calculate_development_time,
    calculate_weight_loss,
    classify_roast,
    fill_forward,
    resolve_actual_temps,
)
from data_persistence import (
    count_roasts,
    load_roast_profiles,
    load_roast_records,
    save_roast_profiles,
    save_roast_records,
)
from validators import (
    validate_bean_name,
    validate_date,
    validate_finished_weight,
    validate_first_crack,
    validate_green_weight,
    validate_profile_name,
    validate_roast_time,
    validate_temperature,
)


class TestDataPersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patcher = mock.patch.object(
            data_persistence,
            "ROAST_RECORDS_PATH",
            Path(self.temp_dir.name) / "roast_records.json",
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_load_roast_records(self):
        records = load_roast_records()
        self.assertIsInstance(records, dict)

    def test_save_roast_records(self):
        records = {
            "04/15/2023": {
                "date": "04/15/2023",
                "bean_name": "Arabica",
                "green_weight": 250,
                "finished_weight": 180,
            }
        }
        save_roast_records(records)
        loaded_records = load_roast_records()
        self.assertIn("04/15/2023", loaded_records)

    def test_save_roast_records_preserves_existing_records(self):
        save_roast_records(
            {
                "04/15/2023": {
                    "date": "04/15/2023",
                    "bean_name": "Arabica",
                    "green_weight": 250,
                    "finished_weight": 180,
                }
            }
        )
        records = load_roast_records()
        records["08/28/2026"] = {
            "date": "08/28/2026",
            "bean_name": "Colombian",
            "green_weight": 205,
            "finished_weight": 178,
        }
        save_roast_records(records)

        reloaded_records = load_roast_records()
        self.assertIn("04/15/2023", reloaded_records)
        self.assertIn("08/28/2026", reloaded_records)

    def test_load_roast_records_corrupted_file_exits(self):
        with open(data_persistence.ROAST_RECORDS_PATH, "w") as file:
            file.write("{not valid json")
        with self.assertRaises(SystemExit):
            load_roast_records()

    def test_count_roasts_missing_file(self):
        self.assertEqual(count_roasts(), 0)

    def test_count_roasts_counts_entries(self):
        save_roast_records(
            {
                "04/15/2023": {"date": "04/15/2023"},
                "08/28/2026": {"date": "08/28/2026"},
            }
        )
        self.assertEqual(count_roasts(), 2)

    def test_count_roasts_corrupted_file_exits(self):
        with open(data_persistence.ROAST_RECORDS_PATH, "w") as file:
            file.write("{not valid json")
        with self.assertRaises(SystemExit):
            count_roasts()


class TestRoastProfilesPersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patcher = mock.patch.object(
            data_persistence,
            "ROAST_PROFILES_PATH",
            Path(self.temp_dir.name) / "roast_profiles.json",
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_load_roast_profiles_missing_file(self):
        profiles = load_roast_profiles()
        self.assertIsInstance(profiles, dict)
        self.assertEqual(profiles, {})

    def test_save_and_load_roast_profiles(self):
        profiles = {
            "profile-1": {
                "name": "City Roast",
                "temps": [None] * 12,
            }
        }
        save_roast_profiles(profiles)
        loaded_profiles = load_roast_profiles()
        self.assertIn("profile-1", loaded_profiles)
        self.assertEqual(loaded_profiles["profile-1"]["name"], "City Roast")

    def test_save_roast_profiles_preserves_existing_profiles(self):
        save_roast_profiles(
            {"profile-1": {"name": "City Roast", "temps": [None] * 12}}
        )
        profiles = load_roast_profiles()
        profiles["profile-2"] = {"name": "Full City", "temps": [None] * 12}
        save_roast_profiles(profiles)

        reloaded_profiles = load_roast_profiles()
        self.assertIn("profile-1", reloaded_profiles)
        self.assertIn("profile-2", reloaded_profiles)

    def test_load_roast_profiles_corrupted_file_exits(self):
        with open(data_persistence.ROAST_PROFILES_PATH, "w") as file:
            file.write("{not valid json")
        with self.assertRaises(SystemExit):
            load_roast_profiles()


class TestValidators(unittest.TestCase):
    def test_validate_date(self):
        self.assertEqual(validate_date("04/15/2023"), "04/15/2023")

    def test_validate_date_rejects_invalid_format(self):
        with self.assertRaises(ValueError):
            validate_date("not-a-date")

    def test_validate_date_rejects_future_date(self):
        with self.assertRaises(ValueError):
            validate_date("12/31/2099")

    def test_validate_bean_name(self):
        self.assertEqual(validate_bean_name("Arabica"), "Arabica")

    def test_validate_bean_name_rejects_empty(self):
        with self.assertRaises(ValueError):
            validate_bean_name("")

    def test_validate_green_weight(self):
        self.assertEqual(validate_green_weight("250"), 250)

    def test_validate_green_weight_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_green_weight("50")

    def test_validate_finished_weight(self):
        self.assertEqual(validate_finished_weight("180", 250), 180)

    def test_validate_finished_weight_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_finished_weight("50", 250)

    def test_validate_roast_time(self):
        self.assertEqual(validate_roast_time("08:30"), 510)

    def test_validate_roast_time_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_roast_time("03:00")

    def test_validate_first_crack(self):
        self.assertEqual(validate_first_crack("06:45", 510), 405)

    def test_validate_first_crack_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_first_crack("09:00", 510)

    def test_validate_profile_name(self):
        self.assertEqual(validate_profile_name("City Roast"), "City Roast")

    def test_validate_profile_name_rejects_empty(self):
        with self.assertRaises(ValueError):
            validate_profile_name("")

    def test_validate_temperature(self):
        self.assertEqual(validate_temperature("350"), 350)

    def test_validate_temperature_allows_blank(self):
        self.assertIsNone(validate_temperature(""))

    def test_validate_temperature_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_temperature("59")
        with self.assertRaises(ValueError):
            validate_temperature("501")

    def test_validate_temperature_rejects_non_numeric(self):
        with self.assertRaises(ValueError):
            validate_temperature("hot")


class TestCalculations(unittest.TestCase):
    def test_calculate_weight_loss(self):
        green_weight = 250
        finished_weight = 180
        expected_loss = ((green_weight - finished_weight) / green_weight) * 100
        self.assertEqual(
            calculate_weight_loss(green_weight, finished_weight), expected_loss
        )

    def test_calculate_weight_loss_raises_for_low_green_weight(self):
        with self.assertRaises(ValueError):
            calculate_weight_loss(99, 50)

    def test_calculate_weight_loss_raises_for_high_green_weight(self):
        with self.assertRaises(ValueError):
            calculate_weight_loss(301, 50)

    def test_calculate_development_time(self):
        total_roast_time = 900
        time_of_first_crack = 800
        development_time = total_roast_time - time_of_first_crack
        self.assertEqual(
            calculate_development_time(total_roast_time, time_of_first_crack),
            development_time,
        )

    def test_calculate_development_time_raises_for_short_roast(self):
        with self.assertRaises(ValueError):
            calculate_development_time(239, 100)

    def test_calculate_development_time_raises_when_first_crack_not_before_total(self):
        with self.assertRaises(ValueError):
            calculate_development_time(500, 500)

    def test_classify_roast(self):
        weight_loss = 14.0
        classification = classify_roast(weight_loss)
        self.assertEqual(classification, "City Plus")

    def test_classify_roast_boundaries(self):
        cases = [
            (13.00, "City Roast"),
            (13.01, "City Plus"),
            (14.50, "City Plus"),
            (14.51, "Full City"),
            (15.50, "Full City"),
            (15.51, "Full City Plus"),
            (16.50, "Full City Plus"),
            (16.51, "Vienna Roast"),
            (18.00, "Vienna Roast"),
            (18.01, "Italian Roast"),
        ]
        for weight_loss, expected in cases:
            with self.subTest(weight_loss=weight_loss):
                self.assertEqual(classify_roast(weight_loss), expected)

    def test_fill_forward_no_gaps(self):
        values = [200, 210, 220]
        self.assertEqual(fill_forward(values), values)

    def test_fill_forward_fills_trailing_gaps(self):
        values = [200, 210, None, None]
        self.assertEqual(fill_forward(values), [200, 210, 210, 210])

    def test_fill_forward_fills_interior_gaps(self):
        values = [200, None, 220, None]
        self.assertEqual(fill_forward(values), [200, 200, 220, 220])

    def test_fill_forward_leading_gaps_stay_none(self):
        values = [None, None, 220]
        self.assertEqual(fill_forward(values), [None, None, 220])

    def test_fill_forward_all_none(self):
        values = [None, None, None]
        self.assertEqual(fill_forward(values), [None, None, None])

    def test_resolve_actual_temps_fills_up_to_total_roast_time(self):
        # 8:30 roast -> 8 whole minutes elapsed; minute 6 carries to 7 and 8.
        entered = [200, 210, 220, 230, 240, 250, None, None, None, None, None, None]
        result = resolve_actual_temps(entered, 510)
        self.assertEqual(
            result,
            [200, 210, 220, 230, 240, 250, 250, 250, None, None, None, None],
        )

    def test_resolve_actual_temps_ignores_entries_past_total_roast_time(self):
        # 6:00 roast -> only the first 6 minutes are meaningful.
        entered = [200, 210, 220, 230, 240, 250, 999, 999, 999, 999, 999, 999]
        result = resolve_actual_temps(entered, 360)
        self.assertEqual(
            result,
            [200, 210, 220, 230, 240, 250, None, None, None, None, None, None],
        )

    def test_resolve_actual_temps_full_length_roast(self):
        entered = [200] + [None] * 11
        result = resolve_actual_temps(entered, 900)
        self.assertEqual(result, [200] * 12)


if __name__ == "__main__":
    unittest.main()
