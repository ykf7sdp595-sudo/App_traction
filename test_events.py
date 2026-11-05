import unittest
from events_ui import selected_source


class EventSelectionTests(unittest.TestCase):
    def test_selection_only_from_target_curve(self):
        self.assertEqual(selected_source({"points": [{"customdata": ["event", "a", 42]}]}, "a", 1, 100), 42)
        for data in (["event", "b", 42], 42, ["event", "a", 999], None):
            self.assertIsNone(selected_source({"points": [{"customdata": data}]}, "a", 1, 100))
        self.assertIsNone(selected_source({"points": [{"customdata": ["event", "a", 10]}, {"customdata": ["event", "a", 20]}]}, "a", 1, 100))
