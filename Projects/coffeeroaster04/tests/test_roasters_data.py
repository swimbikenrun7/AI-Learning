"""Validation tests for the shipped data/roasters.json (Tier 1 fields, SPEC.md "Roasters").

Unlike the other data files, roasters.json is tracked in git and ships with the app, so
a typo in one roaster's entry would otherwise only show up for the user who owns it.
"""

import re
import unittest

from data_persistence import load_roasters

VALUE_FIELDS = [
    "type",
    "calibrated",
    "sources",
    "inferred",
    "notes",
    "green_weight_min_g",
    "green_weight_max_g",
    "green_weight_recommended_g",
    "roast_time_min_s",
    "first_crack_min_s",
    "profile_grid_minutes",
    "temp_unit",
    "temp_source",
    "has_temp_readout",
    "temp_min",
    "temp_max",
]
# Fields whose value may be "inferred" (everything except the descriptive/provenance fields).
DATA_FIELDS = VALUE_FIELDS[5:]
TEMP_SOURCES = {"bean_probe", "inlet_air", "chamber_air", "unspecified", "none"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class TestRoastersData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roasters = load_roasters()

    def for_each_roaster(self, check):
        """Run check(roaster_id, roaster, values) per roaster, each in its own subTest.

        The subTest wraps the assertions themselves, so a failure names the roaster and
        the remaining roasters are still checked.
        """
        for roaster_id, roaster in self.roasters.items():
            with self.subTest(roaster=roaster_id):
                check(roaster_id, roaster, roaster["values"])

    def test_ids_are_slugs_and_names_are_unique_nonblank(self):
        names = []

        def check(roaster_id, roaster, values):
            self.assertRegex(roaster_id, ID_PATTERN)
            self.assertTrue(roaster["name"].strip())
            names.append(roaster["name"])

        self.for_each_roaster(check)
        self.assertEqual(len(names), len(set(names)))

    def test_every_roaster_has_exactly_the_tier1_fields(self):
        def check(roaster_id, roaster, values):
            self.assertEqual(set(roaster), {"name", "values"})
            self.assertEqual(set(values), set(VALUE_FIELDS))

        self.for_each_roaster(check)

    def test_provenance_fields(self):
        def check(roaster_id, roaster, values):
            self.assertIsInstance(values["calibrated"], bool)
            self.assertTrue(values["type"].strip())
            self.assertTrue(values["notes"].strip())
            self.assertGreater(len(values["sources"]), 0)
            for url in values["sources"]:
                self.assertRegex(url, r"^https?://\S+$")
            self.assertEqual(len(values["sources"]), len(set(values["sources"])))

        self.for_each_roaster(check)

    def test_inferred_lists_only_populated_data_fields(self):
        def check(roaster_id, roaster, values):
            self.assertEqual(len(values["inferred"]), len(set(values["inferred"])))
            for field in values["inferred"]:
                self.assertIn(field, DATA_FIELDS)
                self.assertIsNotNone(
                    values[field], f"{field} is listed as inferred but is null"
                )

        self.for_each_roaster(check)

    def test_only_the_sr800_is_calibrated(self):
        calibrated = [
            roaster_id
            for roaster_id, roaster in self.roasters.items()
            if roaster["values"]["calibrated"]
        ]
        self.assertEqual(calibrated, ["fresh-roast-sr800"])

    def test_batch_weights(self):
        def check(roaster_id, roaster, values):
            low = values["green_weight_min_g"]
            high = values["green_weight_max_g"]
            recommended = values["green_weight_recommended_g"]
            self.assertIsInstance(low, int)
            self.assertIsInstance(high, int)
            self.assertGreater(low, 0)
            self.assertLess(low, high)
            if recommended is not None:
                self.assertTrue(low <= recommended <= high)

        self.for_each_roaster(check)

    def test_profile_grid_is_a_positive_whole_number_of_minutes(self):
        def check(roaster_id, roaster, values):
            rows = values["profile_grid_minutes"]
            self.assertIsInstance(rows, int)
            self.assertTrue(1 <= rows <= 60)

        self.for_each_roaster(check)

    def test_fresh_roast_sr_series_use_12_rows(self):
        # Settled decision #4 (to-do.md): the owner's rule for the whole SR series.
        sr_series = [rid for rid in self.roasters if rid.startswith("fresh-roast-sr")]
        self.assertEqual(len(sr_series), 6)
        for roaster_id in sr_series:
            self.assertEqual(
                self.roasters[roaster_id]["values"]["profile_grid_minutes"], 12
            )

    def test_time_floors_fit_inside_the_grid(self):
        def check(roaster_id, roaster, values):
            limit = values["profile_grid_minutes"] * 60
            for field in ("roast_time_min_s", "first_crack_min_s"):
                if values[field] is not None:
                    self.assertIsInstance(values[field], int)
                    self.assertTrue(0 < values[field] < limit)
            if (
                values["roast_time_min_s"] is not None
                and values["first_crack_min_s"] is not None
            ):
                self.assertLess(values["first_crack_min_s"], values["roast_time_min_s"])

        self.for_each_roaster(check)

    def test_temperature_fields_follow_the_readout_flag(self):
        def check(roaster_id, roaster, values):
            self.assertIsInstance(values["has_temp_readout"], bool)
            self.assertIn(values["temp_source"], TEMP_SOURCES)
            if values["has_temp_readout"]:
                self.assertIn(values["temp_unit"], {"F", "C"})
                self.assertNotEqual(values["temp_source"], "none")
                self.assertLess(values["temp_min"], values["temp_max"])
                # Plausible sanity range for the roaster's own unit.
                if values["temp_unit"] == "F":
                    self.assertTrue(
                        32 <= values["temp_min"] and values["temp_max"] <= 700
                    )
                else:
                    self.assertTrue(
                        0 <= values["temp_min"] and values["temp_max"] <= 370
                    )
            else:
                # No readout: no unit or range is invented, and no temperature grid is shown.
                self.assertEqual(values["temp_source"], "none")
                for field in ("temp_unit", "temp_min", "temp_max"):
                    self.assertIsNone(values[field])

        self.for_each_roaster(check)

    def test_inlet_air_roasters_allow_inlet_temperatures(self):
        # Inlet air (e.g. IKAWA) legitimately reaches 290 C, above any bean-temperature cap.
        def check(roaster_id, roaster, values):
            if values["temp_source"] == "inlet_air":
                self.assertEqual(values["temp_unit"], "C")
                self.assertGreaterEqual(values["temp_max"], 290)

        self.for_each_roaster(check)


if __name__ == "__main__":
    unittest.main()
