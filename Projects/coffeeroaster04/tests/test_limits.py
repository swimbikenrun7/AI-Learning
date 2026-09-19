"""Validators and calculation guards that take per-roaster limits (defaults = the original limits)."""

import unittest

from calculations import calculate_development_time, calculate_weight_loss
from validators import (
    validate_finished_weight,
    validate_first_crack,
    validate_green_weight,
    validate_roast_time,
    validate_target_development_time,
    validate_target_first_crack,
    validate_temperature,
)


class TestGreenWeightLimits(unittest.TestCase):
    def test_roaster_limits_are_inclusive(self):
        self.assertEqual(validate_green_weight("113", min_g=113, max_g=227), 113)
        self.assertEqual(validate_green_weight("227", min_g=113, max_g=227), 227)
        for bad in ("112.9", "227.1", "abc", ""):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_green_weight(bad, min_g=113, max_g=227)

    def test_a_small_and_a_large_roaster_both_work(self):
        self.assertEqual(validate_green_weight("60", min_g=20, max_g=60), 60)
        self.assertEqual(validate_green_weight("454", min_g=100, max_g=454), 454)

    def test_error_names_the_roasters_limits(self):
        with self.assertRaises(ValueError) as caught:
            validate_green_weight("5", min_g=113, max_g=227)
        self.assertIn("113", str(caught.exception))
        self.assertIn("227", str(caught.exception))

    def test_defaults_are_the_original_100_to_300(self):
        self.assertEqual(validate_green_weight("100"), 100)
        self.assertEqual(validate_green_weight("300"), 300)
        for bad in ("99.9", "300.1"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_green_weight(bad)


class TestFinishedWeightLimits(unittest.TestCase):
    def test_default_floor_is_100_grams(self):
        with self.assertRaises(ValueError):
            validate_finished_weight("96", 114.0)

    def test_a_roaster_floor_of_one_gram_accepts_a_full_small_batch(self):
        self.assertEqual(validate_finished_weight("96", 114.0, min_g=1), 96)
        self.assertEqual(validate_finished_weight("50", 60.0, min_g=1), 50)

    def test_still_cannot_exceed_the_green_weight_or_be_zero(self):
        for bad in ("61", "0", "-5", "x"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_finished_weight(bad, 60.0, min_g=1)


class TestRoastTimeLimits(unittest.TestCase):
    def test_the_row_count_is_the_inclusive_maximum(self):
        self.assertEqual(validate_roast_time("12:00", max_seconds=720), 720)
        with self.assertRaises(ValueError):
            validate_roast_time("12:01", max_seconds=720)

    def test_a_longer_grid_accepts_longer_roasts(self):
        self.assertEqual(validate_roast_time("20:00", max_seconds=1200), 1200)
        self.assertEqual(validate_roast_time("28:00", max_seconds=1680), 1680)

    def test_a_fast_roaster_can_lower_the_floor(self):
        self.assertEqual(validate_roast_time("3:30", min_seconds=180), 210)
        with self.assertRaises(ValueError):
            validate_roast_time("3:30")

    def test_error_states_the_limits_as_clock_times(self):
        with self.assertRaises(ValueError) as caught:
            validate_roast_time("30:00", max_seconds=720)
        self.assertIn("04:00", str(caught.exception))
        self.assertIn("12:00", str(caught.exception))

    def test_defaults_are_the_original_4_to_under_20_minutes(self):
        self.assertEqual(validate_roast_time("4:00"), 240)
        self.assertEqual(validate_roast_time("19:59"), 1199)
        for bad in ("3:59", "20:00"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_roast_time(bad)
        with self.assertRaises(ValueError) as caught:
            validate_roast_time("30:00")
        self.assertIn("20:00", str(caught.exception))


class TestFirstCrackLimits(unittest.TestCase):
    def test_default_floor_is_4_minutes(self):
        with self.assertRaises(ValueError):
            validate_first_crack("2:30", 300)

    def test_a_roaster_can_lower_the_floor(self):
        self.assertEqual(validate_first_crack("2:30", 300, min_seconds=150), 150)

    def test_must_still_come_before_the_end_of_the_roast(self):
        with self.assertRaises(ValueError):
            validate_first_crack("5:00", 300, min_seconds=150)


class TestTemperatureLimits(unittest.TestCase):
    def test_blank_is_allowed_and_ranges_come_from_the_roaster(self):
        self.assertIsNone(validate_temperature("", min_temp=15, max_temp=300))
        self.assertEqual(validate_temperature("290", min_temp=15, max_temp=300), 290)
        for bad in ("310", "10", "hot"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_temperature(bad, min_temp=15, max_temp=300)

    def test_defaults_are_the_original_60_to_500(self):
        self.assertEqual(validate_temperature("500"), 500)
        with self.assertRaises(ValueError):
            validate_temperature("501")


class TestTargetTimeLimits(unittest.TestCase):
    def test_target_times_cannot_exceed_the_roast_time_limit(self):
        self.assertEqual(validate_target_first_crack("12:00", max_seconds=720), 720)
        self.assertEqual(
            validate_target_development_time("12:00", max_seconds=720), 720
        )
        with self.assertRaises(ValueError):
            validate_target_first_crack("12:01", max_seconds=720)
        with self.assertRaises(ValueError):
            validate_target_development_time("12:01", max_seconds=720)

    def test_blank_is_still_allowed(self):
        self.assertIsNone(validate_target_first_crack("", max_seconds=720))
        self.assertIsNone(validate_target_development_time("", max_seconds=720))

    def test_defaults_are_the_original_limits(self):
        self.assertEqual(validate_target_first_crack("19:59"), 1199)
        with self.assertRaises(ValueError):
            validate_target_first_crack("20:00")
        with self.assertRaises(ValueError):
            validate_target_development_time("20:00")


class TestCalculationGuards(unittest.TestCase):
    def test_weight_loss_guard_defaults_are_unchanged(self):
        with self.assertRaises(ValueError):
            calculate_weight_loss(60, 50)
        with self.assertRaises(ValueError):
            calculate_weight_loss(400, 340)

    def test_weight_loss_accepts_any_range_when_limits_are_opened(self):
        # Saved records were validated when they were saved, so display never re-checks them.
        self.assertAlmostEqual(
            calculate_weight_loss(60, 50, min_g=0, max_g=float("inf")),
            16.6666,
            places=3,
        )

    def test_development_time_guard_defaults_are_unchanged(self):
        with self.assertRaises(ValueError):
            calculate_development_time(210, 150)

    def test_development_time_for_a_short_roast_when_the_floor_is_lowered(self):
        self.assertEqual(calculate_development_time(210, 150, min_total_seconds=0), 60)

    def test_first_crack_must_still_come_before_the_end(self):
        with self.assertRaises(ValueError):
            calculate_development_time(300, 300, min_total_seconds=0)


if __name__ == "__main__":
    unittest.main()
