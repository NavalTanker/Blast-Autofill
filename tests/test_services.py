import unittest
from logic.services import process_data

class TestServices(unittest.TestCase):
    def test_process_data(self):
        self.assertEqual(process_data("test"), "TEST")
        self.assertEqual(process_data("hello world"), "HELLO WORLD")
        self.assertEqual(process_data(""), "")

if __name__ == "__main__":
    unittest.main()
