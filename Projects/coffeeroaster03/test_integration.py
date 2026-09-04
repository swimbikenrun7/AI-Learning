import importlib
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

import data_persistence


class TestIntegration(unittest.TestCase):
    def test_cli_interaction(self):
        # Add a roast, then view roasts, then exit
        inputs = ["1", "04/15/2023", "Arabica", "250", "180", "08:30", "07:00", "2", "4"]

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

        output = captured_stdout.getvalue()
        self.assertIn("Roast added successfully.", output)
        self.assertIn("-" * 40, output)


if __name__ == "__main__":
    unittest.main()
