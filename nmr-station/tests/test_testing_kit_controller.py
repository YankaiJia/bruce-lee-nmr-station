# test_controller.py
import unittest
from unittest.mock import patch, MagicMock
import curses

from testing_kit_controller import Controller
# from .. import testing_kit_controller
# from testing_kit_controller import Controller
 
class TestController(unittest.TestCase):
    def setUp(self):
        self.stdscr = MagicMock()
        self.mock_robot = MagicMock()

    @patch('testing_kit_controller.get_robot')
    @patch('testing_kit_controller.connect_robot')
    @patch('testing_kit_controller.config_robot')
    def test_controller_init(self, mock_config_robot, mock_connect_robot, mock_get_robot):
        mock_get_robot.return_value = self.mock_robot
        controller = Controller(self.stdscr)

        # Assertions to ensure robot functions were called
        mock_get_robot.assert_called_once()
        mock_connect_robot.assert_called_once_with(self.mock_robot)
        mock_config_robot.assert_called_once_with(self.mock_robot)

    @patch('testing_kit_controller.get_robot')
    @patch('testing_kit_controller.connect_robot')
    @patch('testing_kit_controller.config_robot')
    def test_vert_movement_mode_up(self, mock_config_robot, mock_connect_robot, mock_get_robot):
        mock_get_robot.return_value = self.mock_robot
        controller = Controller(self.stdscr)
        controller.model = MagicMock()
        controller.view = MagicMock()

        controller.view.wait_for_key.side_effect = [curses.KEY_UP, ord('x')]
        
        controller.vert_movement_mode()
        

    @patch('testing_kit_controller.get_robot')
    @patch('testing_kit_controller.connect_robot')
    @patch('testing_kit_controller.config_robot')
    def test_vert_movement_mode_down(self, mock_config_robot, mock_connect_robot, mock_get_robot):
        mock_get_robot.return_value = self.mock_robot
        controller = Controller(self.stdscr)
        controller.model = MagicMock()
        controller.view = MagicMock()

        controller.view.wait_for_key.side_effect = [curses.KEY_DOWN, ord('x')]
        
        controller.vert_movement_mode()
    #     controller.model.decrease_z.assert_called_once()

if __name__ == '__main__':
    unittest.main()