import imp
import inspect
import random
import sys
import traceback
try:
    import threading as _threading
    _threading  # for pyflakes
except ImportError:
    import dummy_threading as _threading


from rgkit import rg
from rgkit.gamestate import GameState
from rgkit.settings import settings, AttrDict

sys.modules['rg'] = rg  # preserve backwards compatible robot imports


class NullDevice(object):
    def write(self, msg):
        pass


def init_settings(map_data):
    # I'll get rid of the globals. I promise.
    global settings
    settings.spawn_coords = map_data['spawn']
    settings.obstacles = map_data['obstacle']
    settings.start1 = map_data['start1']
    settings.start2 = map_data['start2']
    rg.set_settings(settings)
    return settings


class Player:
    def __init__(self, code):
        self._module = imp.new_module('usercode%d' % id(self))
        exec code in self._module.__dict__
        self._robot = self._module.__dict__['Robot']()

    def set_player_id(self, player_id):
        self._player_id = player_id

    def reload(self):
        self._robot = self._module.__dict__['Robot']()

    def _get_action(self, game_state, game_info, robot, seed):
        try:
            random.seed(seed)

            self._robot.location = robot.location
            self._robot.hp = robot.hp
            self._robot.player_id = robot.player_id
            self._robot.robot_id = robot.robot_id
            action = self._robot.act(game_info)

            if not game_state.is_valid_action(robot.location, action):
                raise Exception(
                    'Bot {0}: {1} is not a valid action from {2}'.format(
                        robot.robot_id + 1, action, robot.location)
                )

        except Exception:
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
                actions[loc] = self._get_action(game_state,
                                                game_info, robot, seed)

        return actions


class AbstractGame(object):
    def __init__(self, player1, player2, record_actions=False,
                 record_history=False, print_info=False,
                 seed=None, quiet=0):
        global settings
        self._settings = settings
        self._player1 = player1
        self._player1.set_player_id(0)
        self._player2 = player2
        self._player2.set_player_id(1)
        self.state = GameState(self._settings, use_start=True, seed=seed)
        self._record_actions = record_actions
        self._record_history = record_history
        self._print_info = print_info
        self._id_inc = 0
        if seed is None:
            seed = random.randint(0, sys.maxint)
        self.seed = seed
        self._random = random.Random(seed)
        self._quiet = quiet

        self.actions_on_turn = {}  # {turn: {loc: action}}

    def get_actions_on_turn(self, turn):
        if turn in self.actions_on_turn:
            return self.actions_on_turn[turn]
        elif turn < 0:
            return self.actions_on_turn[0]
        elif turn == self._settings.max_turns:
            # get or make dummy data for last turn
            end_turn = self._settings.max_turns
            if end_turn not in self.actions_on_turn:
                self.actions_on_turn[end_turn] = {}
                for loc, log in self.actions_on_turn[end_turn-1].items():
                    dummy = {}
                    dummy['name'] = ''
                    dummy['target'] = None
                    dummy['hp'] = dummy['hp_end'] = log['hp_end']
                    dummy['loc'] = dummy['loc_end'] = log['loc_end']
                    dummy['player'] = log['player']
                    self.actions_on_turn[end_turn][log['loc_end']] = dummy
            return self.actions_on_turn[end_turn]

    def build_players_game_info(self):
        return [self.state.get_game_info(0), self.state.get_game_info(1)]

    def get_robots_actions(self):
        if self._quiet < 3:
            if self._quiet >= 1:
                sys.stdout = NullDevice()
            if self._quiet >= 2:
                sys.stderr = NullDevice()
        seed1 = self._random.randint(0, sys.maxint)
        actions = self._player1.get_actions(self.state, seed1)
        seed2 = self._random.randint(0, sys.maxint)
        actions2 = self._player2.get_actions(self.state, seed2)
        actions.update(actions2)
        if self._quiet < 3:
            if self._quiet >= 1:
                sys.stdout = sys.__stdout__
            if self._quiet >= 2:
                sys.stderr = sys.__stderr__

        return actions

    def make_history(self, actions):
        robots = [[] for i in range(2)]
        for loc, robot in self.state.robots.iteritems():
            robot_info = {}
            props = (self._settings.exposed_properties +
                     self._settings.player_only_properties)
            for prop in props:
                robot_info[prop] = getattr(robot, prop)
            if loc in actions:
                robot_info['action'] = actions[loc]
            robots[robot.player_id].append(robot_info)
        return robots

    # record actions between current state and new state using actions
    # append them to self.actions_on_turn
    def capture_actions(self, actions, new_state):

        def is_new_loc(robot, loc):
            if new_state.is_robot(loc):
                new_robot = new_state.robots[loc]

                if new_robot.robot_id == robot.robot_id:
                    return True

            return False

        log = {}

        for loc, robot in self.state.robots.iteritems():
            log_item = {}

            log_item['name'] = actions[loc][0]
            if len(actions[loc]) > 1:
                log_item['target'] = actions[loc][1]
            else:
                log_item['target'] = None
            log_item['hp'] = robot.hp
            log_item['loc'] = loc
            log_item['player'] = robot.player_id

            # TODO: think of a cleaner approach
            if actions[loc][0] != 'move':
                loc_end = loc
            else:
                destination = actions[loc][1]

                if is_new_loc(robot, destination):
                    loc_end = destination
                else:
                    loc_end = loc

            # robot could have died and get replaced by a spawned one
            if is_new_loc(robot, loc_end):
                log_item['hp_end'] = new_state.robots[loc_end].hp
            else:
                log_item['hp_end'] = 0

            log_item['loc_end'] = loc_end

            log[loc] = log_item

        if self.state.turn % self._settings.spawn_every == 0:
            for loc, robot in new_state.robots.iteritems():
                if loc in self._settings.spawn_coords:
                    log_item = {}
                    log_item['name'] = 'spawn'
                    log_item['target'] = loc
                    log_item['hp'] = robot.hp
                    log_item['hp_end'] = robot.hp
                    log_item['loc'] = loc
                    log_item['loc_end'] = loc
                    log_item['player'] = robot.player_id

                    log[loc] = log_item

        self.actions_on_turn[self.state.turn] = log

    def run_turn(self):
        if self._print_info:
            print (' running turn %d ' % (self.state.turn + 1)).center(70, '-')

        actions = self.get_robots_actions()

        new_state = self.state.apply_actions(actions)

        self.capture_actions(actions, new_state)

        if self._record_history:
            round_history = self.make_history(actions)
            for i in (0, 1):
                self.history[i].append(round_history[i])

        self.state = new_state

    def run_all_turns(self):
        self.finish_running_turns_if_necessary()

    def finish_running_turns_if_necessary(self):
        while self.state.turn < settings.max_turns:
            self.run_turn()

    def get_scores(self):
        self.finish_running_turns_if_necessary()
        return self.state.get_scores()


class Game(AbstractGame):
    def __init__(self, player1, player2, record_actions=False,
                 record_history=False, print_info=False,
                 seed=None, quiet=0):
        super(Game, self).__init__(
            player1, player2, record_actions, record_history,
            print_info, seed, quiet)

        if self._record_history:
            self.history = [list() for i in range(2)]

        if self._record_actions:
            records = [{} for i in range(settings.max_turns)]
            self.actions_on_turn = dict(zip(range(settings.max_turns),
                                            records))
            self.last_locs = {}
            self.last_hps = {}


class PatientList(list):
    """ A list which blocks access to unset items until they are set."""
    def __init__(self, _events):
        self._events = _events

    def forced_get(self, *args):
        return super(PatientList, self).__getitem__(*args)

    def __getitem__(self, key):
        if key >= len(self._events):
            # should raise an IndexError
            super(PatientList, self).__getitem__(key)
            assert False, ("If you see this, then {0} has been misused. " +
                           "The event list contained less items than the " +
                           "current length of the list: {1}".format(
                               self.__class__.__name__, len(self)))
        self._events[key].wait()
        return super(PatientList, self).__getitem__(key)


class ThreadedGame(AbstractGame):
    def __init__(self, player1, player2, record_actions=False,
                 record_history=False, print_info=False,
                 seed=None, quiet=0):
        super(ThreadedGame, self).__init__(
            player1, player2, record_actions, record_history,
            print_info, seed, quiet)

        self.turn_running_lock = _threading.Lock()
        self.per_turn_events = [_threading.Event()
                                for x in xrange(settings.max_turns)]
        self.per_turn_events[0].set()
        self.turn_runner = None

        if self._record_history:
            self.history = [PatientList(self.per_turn_events)
                            for i in range(2)]

        if self._record_actions:
            self.actions_on_turn = PatientList(self.per_turn_events)
            unsafe_actions_on_turn = [dict()
                                      for x in xrange(settings.max_turns)]
            self.actions_on_turn.extend(unsafe_actions_on_turn)
            self.last_locs = {}
            self.last_hps = {}

    def get_actions_on_turn(self, turn):
        # print "threaded get-action"
        if turn < 0:
            turn = 0
        elif turn > self._settings.max_turns:
            turn = self._settings.max_turns
        return self.actions_on_turn.forced_get(turn)

    def run_turn(self):
        super(ThreadedGame, self).run_turn()
        self.per_turn_events[self.state.turn-1].set()

    def run_all_turns(self):
        self.turn_runner = _threading.Thread(
            target=self.finish_running_turns_if_necessary)
        self.turn_runner.daemon = True
        self.turn_runner.start()

    def finish_running_turns_if_necessary(self):
        with self.turn_running_lock:
            while self.state.turn < settings.max_turns:
                self.run_turn()
