import ast
import pkg_resources
import unittest
from rgkit import game
from rgkit.gamestate import GameState

map_data = ast.literal_eval(open(pkg_resources.resource_filename('rgkit', 'maps/default.py')).read())
settings = game.init_settings(map_data)


class TestValid(unittest.TestCase):
    def test_ok(self):
        state = GameState(settings)
        state.add_robot((9, 9), 0)
        self.assertTrue(state.is_valid_action((9, 9), ['guard']))
        self.assertTrue(state.is_valid_action((9, 9), ['suicide']))
        self.assertTrue(state.is_valid_action((9, 9), ['attack', (9, 10)]))
        self.assertTrue(state.is_valid_action((9, 9), ['move', (9, 10)]))

    def test_none(self):
        state = GameState(settings)
        state.add_robot((9, 9), 0)
        self.assertFalse(state.is_valid_action((9, 9), None))

    def test_strange(self):
        state = GameState(settings)
        state.add_robot((9, 9), 0)
        self.assertFalse(state.is_valid_action((9, 9), "ALL YOUR BASE ARE BELONG TO US"))

    def test_wrong_command(self):
        state = GameState(settings)
        state.add_robot((9, 9), 0)
        self.assertFalse(state.is_valid_action((9, 9), ['exterminate']))

    def test_move_to_self(self):
        state = GameState(settings)
        state.add_robot((9, 9), 0)
        self.assertFalse(state.is_valid_action((9, 9), ['move', (9, 9)]))

    def test_move_too_far(self):
        state = GameState(settings)
        state.add_robot((9, 9), 0)
        self.assertFalse(state.is_valid_action((9, 9), ['move', (9, 11)]))

    def test_move_to_obstacle(self):
        state = GameState(settings)
        state.add_robot((2, 5), 0)
        self.assertFalse(state.is_valid_action((2, 5), ['move', (2, 4)]))

    def test_attack_self(self):
        state = GameState(settings)
        state.add_robot((9, 9), 0)
        self.assertFalse(state.is_valid_action((9, 9), ['attack', (9, 9)]))

    def test_attack_too_far(self):
        state = GameState(settings)
        state.add_robot((9, 9), 0)
        self.assertFalse(state.is_valid_action((9, 9), ['attack', (9, 11)]))

    def test_attack_obstacle(self):
        state = GameState(settings)
        state.add_robot((2, 5), 0)
        self.assertFalse(state.is_valid_action((2, 5), ['attack', (2, 4)]))
