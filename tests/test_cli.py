import unittest
from presentation.cli import handle_command
from io import StringIO
import sys

class TestCLI(unittest.TestCase):
    def test_greet_command(self):
        # Redirect stdout to capture print output
        captured_output = StringIO()
        sys.stdout = captured_output
        handle_command("greet")
        sys.stdout = sys.__stdout__  # Reset stdout
        self.assertEqual(captured_output.getvalue().strip(), "Hello, user!")

    def test_unknown_command(self):
        captured_output = StringIO()
        sys.stdout = captured_output
        handle_command("unknown")
        sys.stdout = sys.__stdout__
        self.assertEqual(captured_output.getvalue().strip(), "Unknown command.")

if __name__ == "__main__":
    unittest.main()
