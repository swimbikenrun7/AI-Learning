import sys
import unittest
from io import StringIO

from ui import main


class TestIntegration(unittest.TestCase):
    def test_cli_interaction(self):
        # Simulate user input and capture output
        inputs = ["1", "04/15/2023", "Arabica", "250", "180", "08:30", "07:00"]
        outputs = []
        
        with StringIO() as mock_stdout:
            sys.stdin = StringIO("\n".join(inputs))

            # Capture all output
            main()
            outputs.append(mock_stdout.getvalue())
            
        # Verify the output
        expected_output = "Roast added successfully.\n" + "-" * 40
        self.assertIn(expected_output, outputs[0])

        # Reset stdin and stdout
        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__


if __name__ == "__main__":
    unittest.main()