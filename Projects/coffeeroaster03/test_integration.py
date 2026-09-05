import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import data_persistence
from tui_app import AddRoastScreen, MainScreen, RoastLoggerApp, ViewRoastsScreen


class TestIntegration(unittest.TestCase):
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

    def _run(self, coro):
        return asyncio.run(coro)

    async def _fill_add_roast_form(self, pilot, values):
        app = pilot.app
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
            app = RoastLoggerApp(data_persistence.load_roast_records())
            async with app.run_test(size=(80, 50)) as pilot:
                await pilot.click("#add_roast")
                self.assertIsInstance(app.screen, AddRoastScreen)

                await self._fill_add_roast_form(
                    pilot,
                    ["04/15/2023", "Arabica", "250", "180", "08:30", "07:00"],
                )

                self.assertIsInstance(app.screen, MainScreen)
                self.assertEqual(len(app.roast_records), 1)

        self._run(scenario())

    def test_add_roast_invalid_input_shows_error_and_does_not_save(self):
        async def scenario():
            app = RoastLoggerApp(data_persistence.load_roast_records())
            async with app.run_test(size=(80, 50)) as pilot:
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
            app = RoastLoggerApp(data_persistence.load_roast_records())
            async with app.run_test(size=(80, 50)) as pilot:
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
            app = RoastLoggerApp(data_persistence.load_roast_records())
            async with app.run_test(size=(80, 50)) as pilot:
                await pilot.click("#add_roast")
                await self._fill_add_roast_form(
                    pilot,
                    ["04/15/2023", "Arabica", "250", "180", "08:30", "07:00"],
                )
                await pilot.click("#view_roasts")

                table = app.screen.query_one("#roast_table")
                self.assertEqual(table.row_count, 1)

        self._run(scenario())

    def test_exit_quits_app(self):
        async def scenario():
            app = RoastLoggerApp(data_persistence.load_roast_records())
            async with app.run_test(size=(80, 50)) as pilot:
                await pilot.click("#exit")
                self.assertTrue(app._exit)

        self._run(scenario())


if __name__ == "__main__":
    unittest.main()
