import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import data_persistence
from tui_app import (
    AddEditProfileScreen,
    AddRoastScreen,
    MainScreen,
    ProfileListScreen,
    RoastDetailScreen,
    RoastLoggerApp,
    RoastProfilesMenuScreen,
    ViewRoastsScreen,
)


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.records_patcher = mock.patch.object(
            data_persistence,
            "ROAST_RECORDS_PATH",
            Path(self.temp_dir.name) / "roast_records.json",
        )
        self.profiles_patcher = mock.patch.object(
            data_persistence,
            "ROAST_PROFILES_PATH",
            Path(self.temp_dir.name) / "roast_profiles.json",
        )
        self.records_patcher.start()
        self.profiles_patcher.start()

    def tearDown(self):
        self.records_patcher.stop()
        self.profiles_patcher.stop()
        self.temp_dir.cleanup()

    def _run(self, coro):
        return asyncio.run(coro)

    def _make_app(self):
        roast_profiles = {"profile-1": {"name": "Test Profile", "temps": [None] * 12}}
        return RoastLoggerApp(data_persistence.load_roast_records(), roast_profiles)

    async def _fill_add_roast_form(self, pilot, values, select_profile=True):
        app = pilot.app
        if select_profile:
            table = app.screen.query_one("#select_profile_table")
            table.cursor_coordinate = (0, 0)
            await pilot.press("enter")

        field_ids = [
            "date",
            "bean_name",
            "green_weight",
            "finished_weight",
            "roast_time",
            "first_crack",
        ]
        screen = app.screen
        for field_id, value in zip(field_ids, values):
            screen.query_one(f"#{field_id}").value = value
        await pilot.click("#submit")

    def test_add_roast_success(self):
        async def scenario():
            app = self._make_app()
            async with app.run_test(size=(80, 130)) as pilot:
                await pilot.click("#add_roast")

                await self._fill_add_roast_form(
                    pilot,
                    ["04/15/2023", "Arabica", "250", "180", "08:30", "07:00"],
                )

                self.assertIsInstance(app.screen, MainScreen)
                self.assertEqual(len(app.roast_records), 1)

        self._run(scenario())

    def test_add_roast_invalid_input_shows_error_and_does_not_save(self):
        async def scenario():
            app = self._make_app()
            async with app.run_test(size=(80, 130)) as pilot:
                await pilot.click("#add_roast")

                await self._fill_add_roast_form(
                    pilot,
                    ["04/15/2023", "Arabica", "50", "180", "08:30", "07:00"],
                )

                self.assertIsInstance(app.screen, AddRoastScreen)
                error_text = str(app.screen.query_one("#error").render())
                self.assertIn("Invalid input", error_text)
                self.assertEqual(len(app.roast_records), 0)

        self._run(scenario())

    def test_add_roast_same_date_does_not_overwrite(self):
        async def scenario():
            app = self._make_app()
            async with app.run_test(size=(80, 130)) as pilot:
                await pilot.click("#add_roast")
                await self._fill_add_roast_form(
                    pilot,
                    ["04/15/2023", "Arabica", "250", "180", "08:30", "07:00"],
                )
                await pilot.click("#add_roast")
                await self._fill_add_roast_form(
                    pilot,
                    ["04/15/2023", "Colombian", "220", "150", "09:00", "07:30"],
                )

                self.assertEqual(len(app.roast_records), 2)
                bean_names = {r["bean_name"] for r in app.roast_records.values()}
                self.assertEqual(bean_names, {"Arabica", "Colombian"})

        self._run(scenario())

    def test_view_roasts_with_no_records(self):
        async def scenario():
            app = RoastLoggerApp(data_persistence.load_roast_records())
            async with app.run_test(size=(80, 50)) as pilot:
                await pilot.click("#view_roasts")
                self.assertIsInstance(app.screen, ViewRoastsScreen)
                table = app.screen.query_one("#roast_table")
                self.assertEqual(table.row_count, 0)

        self._run(scenario())

    def test_view_roasts_displays_saved_record(self):
        async def scenario():
            app = self._make_app()
            async with app.run_test(size=(80, 130)) as pilot:
                await pilot.click("#add_roast")
                await self._fill_add_roast_form(
                    pilot,
                    ["04/15/2023", "Arabica", "250", "180", "08:30", "07:00"],
                )
                await pilot.click("#view_roasts")

                table = app.screen.query_one("#roast_table")
                self.assertEqual(table.row_count, 1)
                row = table.get_row_at(0)
                self.assertIn("Test Profile", row)

        self._run(scenario())

    def test_view_roasts_row_select_opens_detail_with_temps(self):
        async def scenario():
            app = self._make_app()
            async with app.run_test(size=(80, 130)) as pilot:
                await pilot.click("#add_roast")
                table = app.screen.query_one("#select_profile_table")
                table.cursor_coordinate = (0, 0)
                await pilot.press("enter")
                app.screen.query_one("#actual_temp_1").value = "300"
                await self._fill_add_roast_form(
                    pilot,
                    ["04/15/2023", "Arabica", "250", "180", "08:30", "07:00"],
                    select_profile=False,
                )

                await pilot.click("#view_roasts")
                roast_table = app.screen.query_one("#roast_table")
                roast_table.cursor_coordinate = (0, 0)
                await pilot.press("enter")

                self.assertIsInstance(app.screen, RoastDetailScreen)
                self.assertEqual(
                    str(app.screen.query_one("#detail_actual_1").render()), "300"
                )
                await pilot.click("#back")
                self.assertIsInstance(app.screen, ViewRoastsScreen)

        self._run(scenario())

    def test_exit_quits_app(self):
        async def scenario():
            app = RoastLoggerApp(data_persistence.load_roast_records())
            async with app.run_test(size=(80, 50)) as pilot:
                await pilot.click("#exit")
                self.assertTrue(app._exit)

        self._run(scenario())


class TestAddRoastWithProfile(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.records_patcher = mock.patch.object(
            data_persistence,
            "ROAST_RECORDS_PATH",
            Path(self.temp_dir.name) / "roast_records.json",
        )
        self.profiles_patcher = mock.patch.object(
            data_persistence,
            "ROAST_PROFILES_PATH",
            Path(self.temp_dir.name) / "roast_profiles.json",
        )
        self.records_patcher.start()
        self.profiles_patcher.start()

    def tearDown(self):
        self.records_patcher.stop()
        self.profiles_patcher.stop()
        self.temp_dir.cleanup()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_add_roast_with_no_profiles_directs_to_create_one(self):
        async def scenario():
            app = RoastLoggerApp(data_persistence.load_roast_records(), {})
            async with app.run_test(size=(80, 50)) as pilot:
                await pilot.click("#add_roast")
                self.assertIn(
                    "No roast profiles",
                    str(app.screen.query_one("#no_profiles_message").render()),
                )
                await pilot.click("#add_profile")
                self.assertIsInstance(app.screen, AddEditProfileScreen)

        self._run(scenario())

    def test_add_roast_snapshots_target_and_truncates_actual_temps(self):
        async def scenario():
            roast_profiles = {
                "profile-1": {
                    "name": "City Roast",
                    "temps": [
                        300,
                        None,
                        None,
                        350,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                    ],
                }
            }
            app = RoastLoggerApp(data_persistence.load_roast_records(), roast_profiles)
            async with app.run_test(size=(80, 130)) as pilot:
                await pilot.click("#add_roast")
                table = app.screen.query_one("#select_profile_table")
                table.cursor_coordinate = (0, 0)
                await pilot.press("enter")

                screen = app.screen
                self.assertIsInstance(screen, AddRoastScreen)
                # Target column pre-populated with carry-forward from the profile.
                self.assertEqual(
                    str(screen.query_one("#target_temp_1").render()), "300"
                )

                screen.query_one("#date").value = "04/15/2023"
                screen.query_one("#bean_name").value = "Arabica"
                screen.query_one("#green_weight").value = "250"
                screen.query_one("#actual_temp_1").value = "290"
                screen.query_one("#actual_temp_2").value = "310"
                # Roast ends at 6:00 -> only minutes 1-6 are meaningful; entry at
                # minute 8 should be ignored even though it's a valid temperature.
                screen.query_one("#actual_temp_8").value = "420"
                screen.query_one("#first_crack").value = "05:00"
                screen.query_one("#roast_time").value = "06:00"
                screen.query_one("#finished_weight").value = "180"
                await pilot.click("#submit")

                self.assertIsInstance(app.screen, MainScreen)
                self.assertEqual(len(app.roast_records), 1)
                record = next(iter(app.roast_records.values()))
                self.assertEqual(record["roast_profile_id"], "profile-1")
                self.assertEqual(
                    record["target_temps"],
                    [300, 300, 300, 350, 350, 350, 350, 350, 350, 350, 350, 350],
                )
                self.assertEqual(
                    record["actual_temps"],
                    [290, 310, 310, 310, 310, 310, None, None, None, None, None, None],
                )

        self._run(scenario())


class TestRoastProfileScreens(unittest.TestCase):
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

    def _run(self, coro):
        return asyncio.run(coro)

    def _make_app(self):
        return RoastLoggerApp({}, data_persistence.load_roast_profiles())

    def test_navigate_to_roast_profiles_menu(self):
        async def scenario():
            app = self._make_app()
            async with app.run_test(size=(80, 110)) as pilot:
                await pilot.click("#roast_profiles")
                self.assertIsInstance(app.screen, RoastProfilesMenuScreen)
                await pilot.click("#back")
                self.assertIsInstance(app.screen, MainScreen)

        self._run(scenario())

    def test_add_profile_success(self):
        async def scenario():
            app = self._make_app()
            async with app.run_test(size=(80, 110)) as pilot:
                await pilot.click("#roast_profiles")
                await pilot.click("#add_profile")
                self.assertIsInstance(app.screen, AddEditProfileScreen)

                screen = app.screen
                screen.query_one("#profile_name").value = "City Roast"
                screen.query_one("#temp_1").value = "300"
                screen.query_one("#temp_5").value = "380"
                await pilot.click("#submit")

                self.assertIsInstance(app.screen, RoastProfilesMenuScreen)
                self.assertEqual(len(app.roast_profiles), 1)
                profile = next(iter(app.roast_profiles.values()))
                self.assertEqual(profile["name"], "City Roast")
                self.assertEqual(profile["temps"][0], 300)
                self.assertEqual(profile["temps"][4], 380)
                self.assertIsNone(profile["temps"][1])

        self._run(scenario())

    def test_add_profile_invalid_temp_shows_error_and_does_not_save(self):
        async def scenario():
            app = self._make_app()
            async with app.run_test(size=(80, 110)) as pilot:
                await pilot.click("#roast_profiles")
                await pilot.click("#add_profile")

                screen = app.screen
                screen.query_one("#profile_name").value = "City Roast"
                screen.query_one("#temp_1").value = "not-a-number"
                await pilot.click("#submit")

                self.assertIsInstance(app.screen, AddEditProfileScreen)
                error_text = str(app.screen.query_one("#error").render())
                self.assertIn("Invalid input", error_text)
                self.assertEqual(len(app.roast_profiles), 0)

        self._run(scenario())

    def test_view_and_edit_existing_profile(self):
        async def scenario():
            app = self._make_app()
            async with app.run_test(size=(80, 110)) as pilot:
                await pilot.click("#roast_profiles")
                await pilot.click("#add_profile")
                app.screen.query_one("#profile_name").value = "City Roast"
                app.screen.query_one("#temp_1").value = "300"
                await pilot.click("#submit")

                await pilot.click("#view_profiles")
                self.assertIsInstance(app.screen, ProfileListScreen)
                table = app.screen.query_one("#profile_table")
                self.assertEqual(table.row_count, 1)

                table.cursor_coordinate = (0, 0)
                await pilot.press("enter")
                self.assertIsInstance(app.screen, AddEditProfileScreen)
                self.assertEqual(
                    app.screen.query_one("#profile_name").value, "City Roast"
                )

                app.screen.query_one("#temp_1").value = "310"
                await pilot.click("#submit")

                self.assertEqual(len(app.roast_profiles), 1)
                profile = next(iter(app.roast_profiles.values()))
                self.assertEqual(profile["temps"][0], 310)

        self._run(scenario())


if __name__ == "__main__":
    unittest.main()
