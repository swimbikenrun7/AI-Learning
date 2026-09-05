import tempfile
import unittest
from pathlib import Path
from unittest import mock

import data_persistence
from calculations import (
    calculate_development_time,
    calculate_weight_loss,
    classify_roast,
)
from data_persistence import count_roasts, load_roast_records, save_roast_records
from validators import (
    validate_bean_name,
    validate_date,
    validate_finished_weight,
    validate_first_crack,
    validate_green_weight,
    validate_roast_time,
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


if __name__ == "__main__":
    unittest.main()
