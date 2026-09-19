import unittest

from data_persistence import load_roasters
from roasters import LEGACY_SETTINGS, TEMP_UNITS, migrate_roaster_ids, settings_for

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
