import unittest

import reaction_manager

class TestReactionManager(unittest.TestCase):
    def test_event_list_volume_change(self):
        # test if the liquid volume change after each event
        # self.assertEqual()
        self.assertEqual(len(reaction_manager.pln.generate_event_list()), 10)