import unittest

from data_persistence import load_roasters
from roasters import (
    LEGACY_SETTINGS,
    TEMP_UNITS,
    chart_opening,
    migrate_roaster_ids,
    settings_for,
)

SR800 = "fresh-roast-sr800"


def roaster(**values):
    return {"name": "Test Roaster", "values": values}


class TestSettingsFor(unittest.TestCase):
    def test_no_roaster_gives_the_original_limits(self):
        settings = settings_for({}, None)
        for field, expected in LEGACY_SETTINGS.items():
            self.assertEqual(settings[field], expected, field)
        self.assertIsNone(settings["roaster_id"])
        self.assertEqual(settings["units"]["symbol"], "°F")

    def test_unknown_roaster_id_falls_back_to_the_original_limits(self):
        settings = settings_for({"a": roaster()}, "nope")
        self.assertEqual(settings["green_weight_max_g"], 300)
        self.assertEqual(settings["roast_time_max_s"], 1199)
        self.assertIsNone(settings["roaster_id"])

    def test_roaster_values_replace_the_defaults(self):
        roasters = {
            "x": roaster(
                green_weight_min_g=50,
                green_weight_max_g=120,
                green_weight_recommended_g=100,
                roast_time_min_s=180,
                first_crack_min_s=150,
                profile_grid_minutes=20,
                has_temp_readout=True,
                temp_unit="C",
                temp_source="bean_probe",
                temp_min=15,
                temp_max=260,
            )
        }
        settings = settings_for(roasters, "x")
        self.assertEqual(settings["roaster_id"], "x")
        self.assertEqual(settings["roaster_name"], "Test Roaster")
        self.assertEqual(settings["green_weight_min_g"], 50)
        self.assertEqual(settings["green_weight_max_g"], 120)
        self.assertEqual(settings["green_weight_recommended_g"], 100)
        self.assertEqual(settings["roast_time_min_s"], 180)
        self.assertEqual(settings["first_crack_min_s"], 150)
        self.assertEqual(settings["profile_grid_minutes"], 20)
        self.assertEqual((settings["temp_min"], settings["temp_max"]), (15, 260))

    def test_max_roast_time_is_the_row_count_in_seconds(self):
        roasters = {"x": roaster(profile_grid_minutes=12)}
        self.assertEqual(settings_for(roasters, "x")["roast_time_max_s"], 720)
        roasters = {"x": roaster(profile_grid_minutes=20)}
        self.assertEqual(settings_for(roasters, "x")["roast_time_max_s"], 1200)

    def test_an_existing_profiles_own_row_count_sets_the_max_roast_time(self):
        roasters = {"x": roaster(profile_grid_minutes=14)}
        self.assertEqual(settings_for(roasters, "x", rows=12)["roast_time_max_s"], 720)

    def test_finished_weight_only_has_to_be_positive_for_a_known_roaster(self):
        self.assertEqual(
            settings_for({"x": roaster()}, "x")["finished_weight_min_g"], 1
        )
        self.assertEqual(settings_for({}, None)["finished_weight_min_g"], 100)

    def test_null_fields_fall_back_to_the_original_value_per_field(self):
        roasters = {"x": roaster(green_weight_max_g=500, roast_time_min_s=None)}
        settings = settings_for(roasters, "x")
        self.assertEqual(settings["green_weight_max_g"], 500)
        self.assertEqual(settings["green_weight_min_g"], 100)
        self.assertEqual(settings["roast_time_min_s"], 240)

    def test_celsius_roaster_gets_celsius_units(self):
        settings = settings_for(
            {"x": roaster(temp_unit="C", has_temp_readout=True)}, "x"
        )
        self.assertEqual(settings["temp_unit"], "C")
        self.assertEqual(settings["units"], TEMP_UNITS["C"])

    def test_roaster_without_a_readout_invents_no_unit_or_range(self):
        settings = settings_for({"x": roaster(has_temp_readout=False)}, "x")
        self.assertFalse(settings["has_temp_readout"])
        self.assertEqual(settings["temp_source"], "none")
        for field in ("temp_unit", "temp_min", "temp_max", "units"):
            self.assertIsNone(settings[field], field)

    def test_chart_anchors_belong_to_the_roaster_and_null_means_none(self):
        with_anchors = roaster(
            chart_start_temp=145, chart_inflection_min=0.5, chart_inflection_temp=270
        )
        settings = settings_for({"x": with_anchors, "y": roaster()}, "x")
        self.assertEqual(settings["chart_start_temp"], 145)
        settings = settings_for({"x": with_anchors, "y": roaster()}, "y")
        self.assertIsNone(settings["chart_start_temp"])
        # Only a profile with no roaster keeps the original anchors.
        self.assertEqual(settings_for({}, None)["chart_start_temp"], 145)

    def test_the_roasters_wizard_data_is_passed_through(self):
        wizard = {"time_to_first_crack_s": {"low": 1, "medium": 2, "high": 3}}
        roasters = {"x": roaster(has_temp_readout=True, wizard=wizard)}
        self.assertEqual(settings_for(roasters, "x")["wizard"], wizard)
        self.assertIsNone(settings_for({"y": roaster()}, "y")["wizard"])
        self.assertIsNone(settings_for({}, None)["wizard"])

    def test_a_roaster_without_a_readout_never_has_a_wizard(self):
        roasters = {"x": roaster(has_temp_readout=False, wizard={"anything": 1})}
        self.assertIsNone(settings_for(roasters, "x")["wizard"])

    def test_the_settings_dict_can_be_changed_without_altering_the_defaults(self):
        settings = settings_for({}, None)
        settings["green_weight_max_g"] = 1
        self.assertEqual(LEGACY_SETTINGS["green_weight_max_g"], 300)


class TestAmbientRanges(unittest.TestCase):
    def test_each_unit_has_a_plausible_range(self):
        for unit, row in TEMP_UNITS.items():
            with self.subTest(unit=unit):
                self.assertLess(row["ambient_min"], row["ambient_max"])

    def test_the_two_units_describe_the_same_temperatures(self):
        f, c = TEMP_UNITS["F"], TEMP_UNITS["C"]
        for key in ("ambient_min", "ambient_max"):
            in_celsius = (f[key] - 32) * 5 / 9
            self.assertAlmostEqual(in_celsius, c[key], delta=1)


class TestSettingsForRealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roasters = load_roasters()

    def test_sr800(self):
        settings = settings_for(self.roasters, SR800)
        self.assertEqual(settings["roaster_name"], "Fresh Roast SR800")
        self.assertEqual(settings["green_weight_min_g"], 113)
        self.assertEqual(settings["green_weight_max_g"], 227)
        self.assertEqual(settings["profile_grid_minutes"], 12)
        self.assertEqual(settings["roast_time_max_s"], 720)
        self.assertEqual(settings["units"]["symbol"], "°F")
        self.assertEqual(settings["chart_start_temp"], 145)

    def test_every_roaster_resolves_to_a_complete_settings_dict(self):
        for roaster_id in self.roasters:
            with self.subTest(roaster=roaster_id):
                settings = settings_for(self.roasters, roaster_id)
                self.assertEqual(settings["roaster_id"], roaster_id)
                self.assertEqual(
                    settings["roast_time_max_s"], settings["profile_grid_minutes"] * 60
                )
                if settings["has_temp_readout"]:
                    self.assertIn(settings["temp_unit"], TEMP_UNITS)
                    self.assertIsNotNone(settings["units"])
                else:
                    self.assertIsNone(settings["units"])

    def test_celsius_roasters_never_carry_fahrenheit_anchors(self):
        # The original anchors (145 F start, 270 F at 30 s) mean nothing on a C scale.
        for roaster_id in self.roasters:
            settings = settings_for(self.roasters, roaster_id)
            if settings["temp_unit"] == "C":
                with self.subTest(roaster=roaster_id):
                    self.assertIsNone(settings["chart_start_temp"])


class TestChartOpening(unittest.TestCase):
    def opening(self, **values):
        base = {"has_temp_readout": True, "temp_unit": "F"}
        return chart_opening(settings_for({"x": roaster(**base, **values)}, "x"))

    def test_chart_anchors_give_the_synthetic_ramp(self):
        anchors = {
            "chart_start_temp": 145,
            "chart_inflection_min": 0.5,
            "chart_inflection_temp": 270,
        }
        self.assertEqual(
            self.opening(start_model="ramp", **anchors),
            {"startTemp": 145, "inflectionMin": 0.5, "inflectionTemp": 270},
        )

    def test_a_profile_with_no_roaster_keeps_the_original_ramp(self):
        self.assertEqual(
            chart_opening(settings_for({}, None)),
            {"startTemp": 145, "inflectionMin": 0.5, "inflectionTemp": 270},
        )

    def test_a_preheat_and_charge_roaster_starts_at_its_charge_temperature(self):
        opening = self.opening(start_model="preheat_charge", charge_temp=167)
        self.assertEqual(
            opening, {"startTemp": 167, "inflectionMin": None, "inflectionTemp": None}
        )

    def test_the_charge_temperature_wins_over_the_preheat_temperature(self):
        opening = self.opening(
            start_model="preheat_charge", charge_temp=167, preheat_temp=230
        )
        self.assertEqual(opening["startTemp"], 167)

    def test_the_preheat_temperature_is_used_when_there_is_no_charge_temperature(self):
        opening = self.opening(start_model="preheat_charge", preheat_temp=230)
        self.assertEqual(opening["startTemp"], 230)

    def test_a_preheat_and_charge_roaster_with_no_temperature_gets_no_opening(self):
        self.assertIsNone(self.opening(start_model="preheat_charge"))

    def test_only_preheat_and_charge_roasters_use_those_temperatures(self):
        for model in ("programmed", "ramp", "none", None):
            with self.subTest(model=model):
                self.assertIsNone(
                    self.opening(start_model=model, preheat_temp=230, charge_temp=200)
                )

    def test_a_roaster_with_no_readout_gets_no_opening(self):
        settings = settings_for({"x": roaster(has_temp_readout=False)}, "x")
        self.assertIsNone(chart_opening(settings))


class TestCoastAndGapSettings(unittest.TestCase):
    def settings(self, **values):
        return settings_for({"x": roaster(**values)}, "x")

    def test_coast_time_defaults_to_unknown(self):
        self.assertIsNone(self.settings()["cooling_coast_seconds"])
        self.assertEqual(
            self.settings(cooling_coast_seconds=20)["cooling_coast_seconds"], 20
        )

    def test_a_gap_is_stated_only_if_a_source_gave_it(self):
        stated = self.settings(min_gap_between_roasts_min=30, inferred=[])
        self.assertTrue(stated["min_gap_stated"])
        inferred = self.settings(
            min_gap_between_roasts_min=30, inferred=["min_gap_between_roasts_min"]
        )
        self.assertFalse(inferred["min_gap_stated"])
        self.assertEqual(inferred["min_gap_between_roasts_min"], 30)

    def test_no_gap_is_never_stated(self):
        self.assertFalse(
            self.settings(min_gap_between_roasts_min=None)["min_gap_stated"]
        )
        self.assertFalse(settings_for({}, None)["min_gap_stated"])


class TestChartOpeningForTheRealRoasters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roasters = load_roasters()

    def opening(self, roaster_id):
        return chart_opening(settings_for(self.roasters, roaster_id))

    def test_sr_machines_with_a_readout_keep_the_synthetic_ramp(self):
        for roaster_id in (
            "fresh-roast-sr540",
            "fresh-roast-sr700",
            "fresh-roast-sr800",
        ):
            with self.subTest(roaster=roaster_id):
                self.assertEqual(
                    self.opening(roaster_id),
                    {"startTemp": 145, "inflectionMin": 0.5, "inflectionTemp": 270},
                )

    def test_roasters_with_a_stated_charge_or_preheat_temperature(self):
        stated = {
            "hottop-kn-8828b-2k": 167,  # the preheat beep: add the beans
            "hottop-kn-8828b-2k-plus": 167,
            "hottop-kn-8828p-2k": 167,
            "aillio-bullet-r1": 160,  # original model preheat
            "aillio-bullet-r1-v2": 230,  # IBTS models
            "quest-m3": 150,  # the handbook's beginner profile
            "sandbox-smart-r1": 200,
        }
        for roaster_id, start in stated.items():
            with self.subTest(roaster=roaster_id):
                self.assertEqual(self.opening(roaster_id)["startTemp"], start)
                self.assertIsNone(self.opening(roaster_id)["inflectionMin"])

    def test_no_temperature_is_borrowed_for_roasters_without_a_source(self):
        for roaster_id in (
            "kaffelogic-nano-7",
            "ikawa-home",
            "gene-cafe-cbr-101",
            "behmor-1600ab",
            "kaldi-mini",
            "kaleido-sniper-m2",
            "huky-500t",
            "roest-s200",
            "whirley-pop-stovetop-popcorn-popper",
        ):
            with self.subTest(roaster=roaster_id):
                self.assertIsNone(self.opening(roaster_id))

    def test_every_opening_start_temperature_fits_the_roasters_range(self):
        for roaster_id in self.roasters:
            settings = settings_for(self.roasters, roaster_id)
            opening = chart_opening(settings)
            if opening is not None:
                with self.subTest(roaster=roaster_id):
                    self.assertTrue(
                        settings["temp_min"]
                        <= opening["startTemp"]
                        <= settings["temp_max"]
                    )

    def test_only_stated_gaps_are_reminders(self):
        def stated(roaster_id):
            return settings_for(self.roasters, roaster_id)["min_gap_stated"]

        self.assertTrue(stated("fresh-roast-sr540"))  # the manual says 30 minutes
        self.assertTrue(stated("behmor-1600ab"))  # the manual says 1 hour
        self.assertTrue(stated("quest-m3"))  # stated as 0: back-to-back is fine
        self.assertTrue(
            stated("fresh-roast-sr800")
        )  # the owner confirmed it for his machine
        self.assertFalse(
            stated("fresh-roast-sr700")
        )  # only assumed from the SR540 manual
        self.assertFalse(stated("gene-cafe-cbr-101"))  # no stated gap at all


class TestMigrateRoasterIds(unittest.TestCase):
    def setUp(self):
        self.roasters = {
            SR800: roaster(has_temp_readout=True, temp_unit="F"),
            "kaldi": roaster(has_temp_readout=True, temp_unit="C"),
        }

    def test_profiles_without_a_roaster_get_the_default(self):
        profiles = {"p1": {"name": "A"}, "p2": {"name": "B", "roaster_id": "kaldi"}}
        result = migrate_roaster_ids(self.roasters, profiles, {}, SR800)
        self.assertEqual(result, (True, False))
        self.assertEqual(profiles["p1"]["roaster_id"], SR800)
        self.assertEqual(profiles["p2"]["roaster_id"], "kaldi")

    def test_records_take_their_profiles_roaster_and_unit(self):
        profiles = {"p2": {"name": "B", "roaster_id": "kaldi"}}
        records = {"r1": {"roast_profile_id": "p2"}}
        result = migrate_roaster_ids(self.roasters, profiles, records, SR800)
        self.assertEqual(result, (False, True))
        self.assertEqual(records["r1"]["roaster_id"], "kaldi")
        self.assertEqual(records["r1"]["temp_unit"], "C")

    def test_records_whose_profile_is_gone_get_the_default(self):
        records = {"r1": {"roast_profile_id": "deleted"}, "r2": {}}
        migrate_roaster_ids(self.roasters, {}, records, SR800)
        for record in records.values():
            self.assertEqual(record["roaster_id"], SR800)
            self.assertEqual(record["temp_unit"], "F")

    def test_a_record_that_already_has_a_roaster_is_left_alone(self):
        records = {
            "r1": {"roaster_id": "kaldi", "temp_unit": "C", "roast_profile_id": "p"}
        }
        profiles = {"p": {"roaster_id": SR800}}
        self.assertEqual(
            migrate_roaster_ids(self.roasters, profiles, records, SR800), (False, False)
        )
        self.assertEqual(records["r1"]["roaster_id"], "kaldi")

    def test_running_it_twice_changes_nothing_the_second_time(self):
        profiles = {"p1": {"name": "A"}}
        records = {"r1": {"roast_profile_id": "p1"}}
        migrate_roaster_ids(self.roasters, profiles, records, SR800)
        snapshot = (dict(profiles["p1"]), dict(records["r1"]))
        self.assertEqual(
            migrate_roaster_ids(self.roasters, profiles, records, SR800), (False, False)
        )
        self.assertEqual((profiles["p1"], records["r1"]), snapshot)

    def test_does_nothing_if_the_default_roaster_is_not_in_the_list(self):
        profiles = {"p1": {"name": "A"}}
        self.assertEqual(migrate_roaster_ids({}, profiles, {}, SR800), (False, False))
        self.assertNotIn("roaster_id", profiles["p1"])


if __name__ == "__main__":
    unittest.main()
