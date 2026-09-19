"""Validation tests for the shipped data/roasters.json (Tier 1 fields, SPEC.md "Roasters").

Unlike the other data files, roasters.json is tracked in git and ships with the app, so
a typo in one roaster's entry would otherwise only show up for the user who owns it.
"""

import re
import unittest
from pathlib import Path

from calculations import classify_roast
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
    "chart_start_temp",
    "chart_inflection_min",
    "chart_inflection_temp",
    "start_model",
    "preheat_temp",
    "charge_temp",
    "controls",
    "cooling",
    "cooling_coast_seconds",
    "min_gap_between_roasts_min",
    "wizard",
]
WIZARD_FIELDS = [
    "time_to_first_crack_s",
    "natural_time_adjust_s",
    "dtr_by_level",
    "profile_start_temp",
    "default_first_crack_temp",
]
START_MODELS = {"ramp", "preheat_charge", "programmed", "none"}
COOLING = {"internal", "external_tray", "manual"}
# The six roast-level names, exactly as the app's own classification calls them.
TIERS = [classify_roast(loss) for loss in (12, 14, 15, 16, 17, 19)]
WIZARD_JS = (
    Path(__file__).resolve().parent.parent / "static" / "js" / "profile_wizard.js"
)
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
                if field.startswith("wizard."):
                    sub = field.split(".", 1)[1]
                    self.assertIn(sub, WIZARD_FIELDS)
                    self.assertIsNotNone(values["wizard"])
                    self.assertIsNotNone(values["wizard"][sub], f"{field} is null")
                    continue
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

    def test_chart_anchors_are_all_set_or_all_null(self):
        anchors = ("chart_start_temp", "chart_inflection_min", "chart_inflection_temp")

        def check(roaster_id, roaster, values):
            given = [values[field] is not None for field in anchors]
            self.assertIn(sum(given), (0, 3))
            if all(given):
                self.assertTrue(values["has_temp_readout"])
                self.assertLess(
                    values["chart_start_temp"], values["chart_inflection_temp"]
                )
                self.assertGreater(values["chart_inflection_min"], 0)

        self.for_each_roaster(check)

    def test_inlet_air_roasters_allow_inlet_temperatures(self):
        # Inlet air (e.g. IKAWA) legitimately reaches 290 C, above any bean-temperature cap.
        def check(roaster_id, roaster, values):
            if values["temp_source"] == "inlet_air":
                self.assertEqual(values["temp_unit"], "C")
                self.assertGreaterEqual(values["temp_max"], 290)

        self.for_each_roaster(check)


class TestRoastersTier2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roasters = load_roasters()

    def for_each_roaster(self, check):
        for roaster_id, roaster in self.roasters.items():
            with self.subTest(roaster=roaster_id):
                check(roaster_id, roaster["values"])

    def test_start_model_follows_the_readout_and_the_chart_anchors(self):
        def check(roaster_id, values):
            self.assertIn(values["start_model"], START_MODELS)
            # No temperature readout means no temperature curve, so no start model.
            self.assertEqual(
                values["start_model"] == "none", not values["has_temp_readout"]
            )
            if values["chart_start_temp"] is not None:
                self.assertEqual(values["start_model"], "ramp")

        self.for_each_roaster(check)

    def test_preheat_and_charge_temperatures_fit_the_roasters_range(self):
        def check(roaster_id, values):
            for field in ("preheat_temp", "charge_temp"):
                if values[field] is None:
                    continue
                self.assertTrue(values["has_temp_readout"])
                self.assertEqual(values["start_model"], "preheat_charge")
                self.assertTrue(
                    values["temp_min"] <= values[field] <= values["temp_max"]
                )

        self.for_each_roaster(check)

    def test_controls_are_well_formed(self):
        def check(roaster_id, values):
            names = [control["name"] for control in values["controls"]]
            self.assertEqual(len(names), len(set(names)))
            for control in values["controls"]:
                self.assertEqual(set(control), {"name", "min", "max", "unit"})
                self.assertTrue(control["name"].strip())
                if control["min"] is not None and control["max"] is not None:
                    self.assertLess(control["min"], control["max"])

        self.for_each_roaster(check)

    def test_cooling_and_the_optional_numbers(self):
        def check(roaster_id, values):
            self.assertIn(values["cooling"], COOLING)
            for field in ("cooling_coast_seconds", "min_gap_between_roasts_min"):
                if values[field] is not None:
                    self.assertIsInstance(values[field], int)
                    self.assertGreaterEqual(values[field], 0)

        self.for_each_roaster(check)

    def test_a_wizard_exists_exactly_when_there_is_a_temperature_readout(self):
        def check(roaster_id, values):
            self.assertEqual(values["wizard"] is not None, values["has_temp_readout"])

        self.for_each_roaster(check)

    def test_wizard_values_are_consistent(self):
        def check(roaster_id, values):
            wizard = values["wizard"]
            if wizard is None:
                return
            self.assertEqual(set(wizard), set(WIZARD_FIELDS))
            times = wizard["time_to_first_crack_s"]
            self.assertEqual(set(times), {"low", "medium", "high"})
            self.assertTrue(times["low"] <= times["medium"] <= times["high"])
            limit = values["profile_grid_minutes"] * 60
            self.assertTrue(0 < times["high"] < limit)
            dtr = wizard["dtr_by_level"]
            self.assertEqual(list(dtr), TIERS)
            ratios = list(dtr.values())
            self.assertEqual(ratios, sorted(ratios))
            self.assertTrue(all(0 < ratio < 0.5 for ratio in ratios))
            adjust = wizard["natural_time_adjust_s"]
            if adjust is not None:
                self.assertIsInstance(adjust, int)
                self.assertLess(abs(adjust), times["medium"])
            for field in ("profile_start_temp", "default_first_crack_temp"):
                if wizard[field] is not None:
                    self.assertTrue(
                        values["temp_min"] <= wizard[field] <= values["temp_max"]
                    )
            if None not in (
                wizard["profile_start_temp"],
                wizard["default_first_crack_temp"],
            ):
                self.assertLess(
                    wizard["profile_start_temp"], wizard["default_first_crack_temp"]
                )

        self.for_each_roaster(check)

    def test_the_sr_series_share_the_calibrated_wizard_table_and_no_one_else_does(self):
        sr800 = self.roasters["fresh-roast-sr800"]["values"]["wizard"]["dtr_by_level"]
        for roaster_id, roaster in self.roasters.items():
            wizard = roaster["values"]["wizard"]
            if wizard is None:
                continue
            with self.subTest(roaster=roaster_id):
                self.assertEqual(
                    wizard["dtr_by_level"] == sr800,
                    roaster_id.startswith("fresh-roast-sr"),
                )

    def test_the_wizard_script_takes_its_numbers_from_the_data_not_from_constants(self):
        # The wizard used to carry the SR800's numbers in the script itself; they now come
        # from the roaster's data via the page config. Fail if that comes back.
        script = WIZARD_JS.read_text()
        self.assertIn('getElementById("wizard-config")', script)
        for name in (
            "ROAST_LEVEL_DTR",
            "MAILLARD_TIME_SECONDS",
            "NATURAL_TIME_ADJUST_SECONDS",
            "PROFILE_START_TEMP",
        ):
            self.assertNotIn(name, script)
        self.assertNotIn("Array(12)", script)
        self.assertNotIn("<= 12", script)

    def test_only_the_sr800_has_a_stated_wizard(self):
        for roaster_id, roaster in self.roasters.items():
            values = roaster["values"]
            if values["wizard"] is None:
                continue
            stated = [
                f"wizard.{sub}"
                for sub in WIZARD_FIELDS
                if values["wizard"][sub] is not None
                and f"wizard.{sub}" not in values["inferred"]
            ]
            with self.subTest(roaster=roaster_id):
                if roaster_id == "fresh-roast-sr800":
                    self.assertEqual(len(stated), len(WIZARD_FIELDS))
                # Only Kaffelogic, Hottop, Kaldi and Sandbox state a first-crack time or temperature.
                elif (
                    "wizard.time_to_first_crack_s" in stated
                    or "wizard.default_first_crack_temp" in stated
                ):
                    self.assertTrue(
                        roaster_id.startswith(
                            ("kaffelogic", "hottop", "kaldi", "quest", "sandbox")
                        )
                    )


if __name__ == "__main__":
    unittest.main()
