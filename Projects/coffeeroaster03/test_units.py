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
from user_input import (
    get_bean_name,
    get_date,
    get_finished_weight,
    get_green_weight,
    get_roast_time,
    get_time_of_first_crack,
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


class TestUserInput(unittest.TestCase):
    @mock.patch("builtins.input")
    def test_get_date(self, mock_input):
        mock_input.return_value = "04/15/2023"
        date = get_date()
        self.assertEqual(date, "04/15/2023")

    @mock.patch("builtins.input")
    def test_get_date_retries_on_invalid_format(self, mock_input):
        mock_input.side_effect = ["not-a-date", "04/15/2023"]
        date = get_date()
        self.assertEqual(date, "04/15/2023")

    @mock.patch("builtins.input")
    def test_get_date_rejects_future_date(self, mock_input):
        mock_input.side_effect = ["12/31/2099", "04/15/2023"]
        date = get_date()
        self.assertEqual(date, "04/15/2023")

    @mock.patch("builtins.input")
    def test_get_bean_name(self, mock_input):
        mock_input.return_value = "Arabica"
        bean_name = get_bean_name()
        self.assertEqual(bean_name, "Arabica")

    @mock.patch("builtins.input")
    def test_get_green_weight(self, mock_input):
        mock_input.return_value = "250"
        green_weight = get_green_weight()
        self.assertEqual(green_weight, 250)

    @mock.patch("builtins.input")
    def test_get_green_weight_retries_on_invalid_input(self, mock_input):
        mock_input.side_effect = ["50", "250"]
        green_weight = get_green_weight()
        self.assertEqual(green_weight, 250)

    @mock.patch("builtins.input")
    def test_get_finished_weight(self, mock_input):
        mock_input.return_value = "180"
        finished_weight = get_finished_weight(250)
        self.assertEqual(finished_weight, 180)

    @mock.patch("builtins.input")
    def test_get_finished_weight_retries_on_invalid_input(self, mock_input):
        mock_input.side_effect = ["50", "180"]
        finished_weight = get_finished_weight(250)
        self.assertEqual(finished_weight, 180)

    @mock.patch("builtins.input")
    def test_get_roast_time(self, mock_input):
        mock_input.return_value = "08:30"
        total_roast_time = get_roast_time()
        self.assertEqual(total_roast_time, 510)

    @mock.patch("builtins.input")
    def test_get_roast_time_retries_on_invalid_input(self, mock_input):
        mock_input.side_effect = ["03:00", "08:30"]
        total_roast_time = get_roast_time()
        self.assertEqual(total_roast_time, 510)

    @mock.patch("builtins.input")
    def test_get_time_of_first_crack(self, mock_input):
        mock_input.return_value = "06:45"
        time_of_first_crack = get_time_of_first_crack(510)
        self.assertEqual(time_of_first_crack, 405)

    @mock.patch("builtins.input")
    def test_get_time_of_first_crack_retries_on_invalid_input(self, mock_input):
        mock_input.side_effect = ["09:00", "06:45"]
        time_of_first_crack = get_time_of_first_crack(510)
        self.assertEqual(time_of_first_crack, 405)


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
