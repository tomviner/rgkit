import imp
import os
import random
import sys
import traceback
try:
    import threading
except ImportError:
    import dummy_threading as threading


from rgkit import rg
from rgkit.gamestate import GameState
from rgkit.settings import settings

sys.modules['rg'] = rg  # preserve backwards compatible robot imports


class NullDevice(object):
    def write(self, msg):
        pass

    def flush(self):
        pass


class Player(object):
    def __init__(self, file_name=None, robot=None, code=None, name=None):
        """
        One of these arguments must be provided:
        file_name -- path to file containing a robot
        robot -- instance of a robot
        code -- source code containing a robot
        name argument can be used to set robot's name
        """
        self._player_id = None  # must be set using set_player_id

        self._code = code
        if file_name is not None:
            with open(file_name) as f:
                self._code = f.read()
            self._name = os.path.splitext(
                os.path.basename(file_name))[0]
        if name is not None:
            self._name = name
        self.load(robot)

    def load(self, robot=None):
        if robot is not None:
            self._name = str(robot.__class__).split('.')[-1]
            self._robot = robot
        elif self._code:
            self._module = imp.new_module('usercode%d' % id(self))
            exec self._code in self._module.__dict__
            self._robot = self._module.Robot()
        else:
            # No way to reload robot...
            pass

    def set_player_id(self, player_id):
        self._player_id = player_id

    @staticmethod
    def _validate_type(robot, var_name, obj, types):
        if type(obj) not in types:
            raise Exception(
                "Bot {0}: {1} of type {2} is not valid.".format(
                    robot.robot_id, var_name, type(obj).__name__)
            )

    @staticmethod
    def _validate_length(robot, var_name, obj, lengths):
        if len(obj) not in lengths:
            # assumes that type of obj has already been validated and so
            # __repr__ has not been overwritten
            raise Exception(
                "Bot {0}: {1} of length {2} is not valid.".format(
                    robot.robot_id, var_name, len(obj))
            )

    @staticmethod
    def _validate_action(robot, action):
        """
        Need to be VERY CAREFUL here not to call any built-in functions on
        'action' unless it is known to be completely safe. A malicious bot may
        return an object with overwritten built-in functions that run arbitrary
        code.
        """
        Player._validate_type(robot, 'action', action, (list, tuple))
        Player._validate_length(robot, 'action', action, (1, 2))
        Player._validate_type(robot, 'action[0]', action[0], (str,))
        if action[0] in ('move', 'attack'):
            if len(action) != 2:
                raise Exception(
                    'Bot {0}: {1} requires a location as well.'.format(
                        robot.robot_id, action)
                )
            Player._validate_type(robot, 'action[1]', action[1], (list, tuple))
            Player._validate_length(robot, 'action[1]', action[1], (2,))
            Player._validate_type(
                robot, 'action[1][0]', action[1][0], (int, long, float))
            Player._validate_type(
                robot, 'action[1][1]', action[1][1], (int, long, float))
            valid_locs = rg.locs_around(
                robot.location, filter_out=['invalid', 'obstacle'])
            if action[1] not in valid_locs:
                raise Exception(
                    'Bot {0}: {1} is not a valid action.'.format(
                        robot.robot_id, action)
                )
        elif action[0] not in ('guard', 'suicide'):
            raise Exception('Bot %d: action must be one of "guard", "suicide",'
                            '"move", or "attack".')

    def _get_action(self, game_state, game_info, robot, seed):
        try:
            random.seed(seed)
            # Server requires knowledge of seed
            game_info.seed = seed

            self._robot.location = robot.location
            self._robot.hp = robot.hp
            self._robot.player_id = robot.player_id
            self._robot.robot_id = robot.robot_id
            action = self._robot.act(game_info)

            Player._validate_action(robot, action)

            if action[0] in ('move', 'attack'):
                action = (
                    action[0],
                    (int(action[1][0]), int(action[1][1]))
                )
            elif action[0] in ('guard', 'suicide'):
                action = (action[0],)

        except:
            traceback.print_exc(file=sys.stdout)
            action = ['guard']

        return action

    # returns map (loc) -> (action) for all bots of this player
    # 'fixes' invalid actions
    def get_actions(self, game_state, seed):
        game_info = game_state.get_game_info(self._player_id)
        actions = {}

        for loc, robot in game_state.robots.iteritems():
            if robot.player_id == self._player_id:
                # Every act call should get a different random seed
                actions[loc] = self._get_action(
                    game_state, game_info, robot,
                    seed=str(seed) + '-' + str(robot.robot_id))

        return actions

    def name(self):
        return self._name


class Game(object):
    def __init__(self, players, record_actions=False, record_history=False,
                 print_info=False, seed=None, quiet=0, delta_callback=None,
                 symmetric=True):
        self._players = players
        for i, player in enumerate(self._players):
            player.set_player_id(i)
        self._record_actions = record_actions
        self._record_history = record_history
        self._print_info = print_info
        if seed is None:
            seed = random.randint(0, settings.max_seed)
        self.seed = str(seed)
        self._random = random.Random(self.seed)
        self._quiet = quiet
        self._delta_callback = delta_callback
        self._state = GameState(use_start=True, seed=self.seed,
                                symmetric=symmetric)

        self._actions_on_turn = {}
        self._states = {}
        self.history = []  # TODO: make private

    # actions_on_turn = {loc: log_item}
    # log_item = {
    #     'name': action_name,
    #     'target': action_target or None,
    #     'loc': loc,
    #     'hp': hp,
    #     'player': player_id,
    #     'loc_end': loc_end,
    #     'hp_end': hp_end
    # }
    #
    # or dummy if turn == settings.max_turn
    def get_actions_on_turn(self, turn):
        assert self._record_actions
        return self._actions_on_turn[turn]

    def get_state(self, turn):
        return self._states[turn]

    def _save_actions_on_turn(self, actions_on_turn, turn):
        self._actions_on_turn[turn] = actions_on_turn

    def _save_state(self, state, turn):
        self._states[turn] = state

    def _get_robots_actions(self):
        if self._quiet >= 1:
            sys.stdout = NullDevice()
        if self._quiet >= 2:
            sys.stderr = NullDevice()

        actions = {}
        for player in self._players:
            seed = self._random.randint(0, settings.max_seed)
            actions.update(player.get_actions(self._state, seed))

        if self._quiet >= 1:
            sys.stdout = sys.__stdout__
        if self._quiet >= 2:
            sys.stderr = sys.__stderr__

        return actions

    def _make_history(self, actions):
        '''
        An aggregate of all bots and their actions this turn.

        Stores a list of each player's bots at the start of this turn and
        the actions they each performed this turn. Newly spawned bots have no
        actions.
        '''
        robots = []
        for loc, robot in self._state.robots.iteritems():
            robot_info = {
                'location': loc,
                'hp': robot.hp,
                'player_id': robot.player_id,
                'robot_id': robot.robot_id,
            }
            if loc in actions:
                robot_info['action'] = actions[loc]
            robots.append(robot_info)
        return robots

    def _calculate_actions_on_turn(self, delta, actions):
        actions_on_turn = {}

        for delta_info in delta:
            loc = delta_info.loc

            if loc in actions:
                name = actions[loc][0]
                if name in ['move', 'attack']:
                    target = actions[loc][1]
                else:
                    target = None
            else:
                name = 'spawn'
                target = None

            # note that a spawned bot may overwrite an existing bot
            actions_on_turn[loc] = {
                'name': name,
                'target': target,
                'loc': loc,
                'hp': delta_info.hp,
                'player': delta_info.player_id,
                'loc_end': delta_info.loc_end,
                'hp_end': delta_info.hp_end
            }

        return actions_on_turn

    def run_turn(self):
        if self._print_info:
            print (' running turn %d ' % (self._state.turn)).center(70, '-')

        actions = self._get_robots_actions()

        delta = self._state.get_delta(actions)

        if self._record_actions:
            actions_on_turn = self._calculate_actions_on_turn(delta, actions)
            self._save_actions_on_turn(actions_on_turn, self._state.turn)

        new_state = self._state.apply_delta(delta)

        if self._delta_callback is not None and self._state.turn > 1:
            self._delta_callback(delta, new_state)

        self._save_state(new_state, new_state.turn)

        if self._record_history:
            self.history.append(self._make_history(actions))

        self._state = new_state

    def run_all_turns(self):
        assert self._state.turn == 0

        if self._print_info:
            print ('Match seed: {0}'.format(self.seed))

        self._save_state(self._state, 0)

        while self._state.turn < settings.max_turns:
            self.run_turn()

        # create last turn's state for server history
        if self._record_history:
            self.history.append(self._make_history({}))

        # create dummy data for last turn
        # TODO: render should be cleverer
        actions_on_turn = {}

        for loc, robot in self._state.robots.iteritems():
            log_item = {
                'name': '',
                'target': None,
                'loc': loc,
                'hp': robot.hp,
                'player': robot.player_id,
                'loc_end': loc,
                'hp_end': robot.hp
            }

            actions_on_turn[loc] = log_item

        self._save_actions_on_turn(actions_on_turn, settings.max_turns)

    def get_scores(self):
        return self.get_state(settings.max_turns).get_scores()


class ThreadedGame(Game):
    def __init__(self, *args, **kwargs):
        super(ThreadedGame, self).__init__(*args, **kwargs)

        # events set when actions_on_turn are calculated
        self._has_actions_on_turn = [threading.Event()
                                     for _ in xrange(settings.max_turns + 1)]

        # events set when state are calculated
        self._has_state = [threading.Event()
                           for _ in xrange(settings.max_turns + 1)]

    def get_actions_on_turn(self, turn):
        self._has_actions_on_turn[turn].wait()
        return super(ThreadedGame, self).get_actions_on_turn(turn)

    def get_state(self, turn):
        self._has_state[turn].wait()
        return super(ThreadedGame, self).get_state(turn)

    def _save_actions_on_turn(self, actions_on_turn, turn):
        super(ThreadedGame, self)._save_actions_on_turn(actions_on_turn, turn)
        self._has_actions_on_turn[turn].set()

    def _save_state(self, state, turn):
        super(ThreadedGame, self)._save_state(state, turn)
        self._has_state[turn].set()

    def run_all_turns(self):
        lock = threading.Lock()

        def task():
            with lock:
                super(ThreadedGame, self).run_all_turns()

        turn_runner = threading.Thread(target=task)
        turn_runner.daemon = True
        turn_runner.start()
