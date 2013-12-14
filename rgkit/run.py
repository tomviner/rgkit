#!/usr/bin/env python2

import argparse
import ast
import imp
import inspect
import itertools
import pkg_resources
import sys

_is_multiprocessing_supported = True
try:
    from multiprocessing import Pool
except ImportError:
    # the OS does not support it. See http://bugs.python.org/issue3770
    _is_multiprocessing_supported = False

try:
    imp.find_module('rgkit')
except ImportError:
    # force rgkit to appear as a module when run from current directory
    from os.path import dirname, abspath
    cdir = dirname(abspath(inspect.getfile(inspect.currentframe())))
    parentdir = dirname(cdir)
    sys.path.insert(0, parentdir)

from rgkit import game


parser = argparse.ArgumentParser(description="Robot game execution script.")
parser.add_argument("usercode1",
                    help="File containing first robot class definition.")
parser.add_argument("usercode2",
                    help="File containing second robot class definition.")
parser.add_argument("-m", "--map",
                    help="User-specified map file.",
                    type=argparse.FileType('r'),
                    default=pkg_resources.resource_filename('rgkit',
                                                            'maps/default.py'))
parser.add_argument("-c", "--count", type=int,
                    default=1,
                    help="Game count, default: 1")
parser.add_argument("-A", "--no-animate", action="store_false",
                    default=True,
                    help="Disable animations in rendering.")
group = parser.add_mutually_exclusive_group()
group.add_argument("-H", "--headless", action="store_true",
                   default=False,
                   help="Disable rendering game output.")
group.add_argument("-T", "--play-in-thread", action="store_true",
                   default=False,
                   help="Separate GUI thread from robot move calculations.")
parser.add_argument("--game-seed", default='initialseed',
                    help="Appended with game countfor per-match seeds.")
parser.add_argument("--match-seeds", nargs='*',
                    help="Used for random seed of the first matches in order.")


def make_player(fname):
    try:
        with open(fname) as f:
            return game.Player(f.read())
    except IOError, msg:
        if pkg_resources.resource_exists('rgkit', fname):
            with open(pkg_resources.resource_filename('rgkit', fname)) as f:
                return game.Player(f.read())
        raise IOError(msg)


def play(players, print_info=True, animate_render=True, play_in_thread=False,
         match_seed=None):
    if play_in_thread:
        g = game.ThreadedGame(*players,
                              print_info=print_info,
                              record_actions=True,
                              record_history=True,
                              seed=match_seed)
    else:
        g = game.Game(*players,
                      print_info=print_info,
                      record_actions=True,
                      record_history=True,
                      seed=match_seed)

    if print_info:
        print('Match seed: {}'.format(g.seed))

        # only import render if we need to render the game;
        # this way, people who don't have tkinter can still
        # run headless
        from rgkit import render

        g.run_all_turns()
        render.Render(g, game.settings, animate_render)
        print g.history

    return g.get_scores()


def test_runs_sequentially(args):
    players = [make_player(args.usercode1), make_player(args.usercode2)]
    scores = []
    for i in xrange(args.count):
        # A sequential, deterministic seed is used for each match that can be
        # overridden by user provided ones.
        match_seed = args.game_seed + str(i)
        if args.match_seeds and i < len(args.match_seeds):
            match_seed = args.match_seeds[i]
        scores.append(
            play(players,
                 not args.headless,
                 args.no_animate,
                 args.play_in_thread,
                 match_seed=match_seed)
        )
        print scores[-1]
    return scores


def task(data):
    (usercode1,
     usercode2,
     headless,
     no_animate,
     play_in_thread,
     match_seed) = data

    result = play(
        [
            make_player(usercode1),
            make_player(usercode2)
        ],
        not headless,
        no_animate,
        play_in_thread,
        match_seed=match_seed,
    )
    print '{0} - seed: {1}'.format(result, match_seed)
    return result


def test_runs_concurrently(args):
    data = []
    for i in xrange(args.count):
        match_seed = args.game_seed + str(i)
        if args.match_seeds and i < len(args.match_seeds):
            match_seed = args.match_seeds[i]
        data.append([
            args.usercode1,
            args.usercode2,
            args.headless,
            args.no_animate,
            args.play_in_thread,
            match_seed,
        ])
    return Pool().map(task, data, 1)


def main():
    args = parser.parse_args()

    map_data = ast.literal_eval(args.map.read())
    game.init_settings(map_data)
    print('Game seed: {0}'.format(args.game_seed))

    runner = test_runs_sequentially
    if _is_multiprocessing_supported and args.count > 1:
        runner = test_runs_concurrently
    scores = runner(args)

    if args.count > 1:
        p1won = sum(p1 > p2 for p1, p2 in scores)
        p2won = sum(p2 > p1 for p1, p2 in scores)
        print [p1won, p2won, args.count - p1won - p2won]


if __name__ == '__main__':
    main()
