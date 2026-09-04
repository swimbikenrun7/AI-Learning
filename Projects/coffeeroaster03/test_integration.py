import importlib
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

import data_persistence


class TestIntegration(unittest.TestCase):
    def _run_cli(self, inputs):
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(
                data_persistence,
                "ROAST_RECORDS_PATH",
                Path(temp_dir) / "roast_records.json",
            ):
                import ui

                importlib.reload(ui)

                sys.stdin = StringIO("\n".join(inputs))
                sys.stdout = captured_stdout = StringIO()
                try:
                    ui.main()
                finally:
                    sys.stdin = sys.__stdin__
                    sys.stdout = sys.__stdout__

        return captured_stdout.getvalue()

    def test_cli_interaction(self):
        # Add a roast, then view roasts, then exit
        inputs = ["1", "04/15/2023", "Arabica", "250", "180", "08:30", "07:00", "2", "4"]
        output = self._run_cli(inputs)

        self.assertIn("Roast added successfully.", output)
        self.assertIn("-" * 40, output)

    def test_add_roast_retries_on_invalid_input(self):
        # Green weight "50" is below the valid range and should be re-prompted
        inputs = ["1", "04/15/2023", "Arabica", "50", "250", "180", "08:30", "07:00", "4"]
        output = self._run_cli(inputs)

        self.assertIn("Roast added successfully.", output)

    def test_invalid_menu_choice_reprompts(self):
        output = self._run_cli(["9", "4"])
        self.assertIn("Invalid choice. Please try again.", output)

    def test_view_roasts_with_no_records(self):
        output = self._run_cli(["2", "4"])
        self.assertIn("Classification", output)

    def test_count_roasts_option(self):
        output = self._run_cli(["3", "4"])
        self.assertIn("Total number of stored roasts: 0", output)

    def test_add_roast_same_date_does_not_overwrite(self):
        inputs = [
            "1", "04/15/2023", "Arabica", "250", "180", "08:30", "07:00",
            "1", "04/15/2023", "Colombian", "220", "150", "09:00", "07:30",
            "2",
            "3",
            "4",
        ]
        output = self._run_cli(inputs)

        self.assertIn("Arabica", output)
        self.assertIn("Colombian", output)
        self.assertIn("Total number of stored roasts: 2", output)


if __name__ == "__main__":
    unittest.main()
