#!/usr/bin/env python2

import argparse
from argparse import RawTextHelpFormatter
import ast
import imp
import inspect
import itertools
import pkg_resources
import random
import sys
import os

_is_multiprocessing_supported = True
try:
    import multiprocessing
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

parser = argparse.ArgumentParser(description="Robot game execution script.",
                                 formatter_class=RawTextHelpFormatter)
parser.add_argument("player1",
                    help="File containing first robot class definition.")
parser.add_argument("player2",
                    help="File containing second robot class definition.")
parser.add_argument("-m", "--map",
                    help="User-specified map file.",
                    type=argparse.FileType('r'),
                    default=pkg_resources.resource_filename('rgkit',
                                                            'maps/default.py'))
parser.add_argument("-c", "--count", type=int,
                    default=1,
                    help="Game count, default: 1")
parser.add_argument("-A", "--animate", action="store_true",
                    default=False,
                    help="Enable animations in rendering.")
parser.add_argument("-q", "--quiet", action="count",
                    help="Quiet execution.\n\
-q : suppresses bot stdout\n\
-qq: suppresses bot stdout and stderr\n\
-qqq: supresses all rgkit and bot output")
group = parser.add_mutually_exclusive_group()
group.add_argument("-H", "--headless", action="store_true",
                   default=False,
                   help="Disable rendering game output.")
group.add_argument("-T", "--play-in-thread", action="store_true",
                   default=False,
                   help="Separate GUI thread from robot move calculations.")
parser.add_argument("--game-seed",
                    default=random.randint(0, sys.maxint),
                    help="Appended with game countfor per-match seeds.")
parser.add_argument("--match-seeds", nargs='*',
                    help="Used for random seed of the first matches in order.")


def mute_all():
    sys.stdout = game.NullDevice()
    sys.stderr = game.NullDevice()


def unmute_all():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__


def make_player(fname):
    try:
        with open(fname) as f:
            return game.Player(code=f.read())
    except IOError, msg:
        if pkg_resources.resource_exists('rgkit', fname):
            with open(pkg_resources.resource_filename('rgkit', fname)) as f:
                return game.Player(code=f.read())
        raise IOError(msg)


def play(players, print_info=True, animate_render=False, play_in_thread=False,
         match_seed=None, names=["Red", "Green"], quiet=0):
    if play_in_thread:
        g = game.ThreadedGame(*players,
                              print_info=print_info,
                              record_actions=True,
                              record_history=True,
                              seed=match_seed, quiet=quiet)
    else:
        g = game.Game(*players,
                      print_info=print_info,
                      record_actions=True,
                      record_history=True,
                      seed=match_seed, quiet=quiet)

    if print_info:
        # only import render if we need to render the game;
        # this way, people who don't have tkinter can still
        # run headless
        from rgkit import render

        g.run_all_turns()
        #print "rendering %s animations" % ("with"
        #                                   if animate_render else "without")
        render.Render(g, game.settings, animate_render, names=names)

    return g.get_scores()


def test_runs_sequentially(args):
    players = [make_player(args.player1), make_player(args.player2)]
    names = [bot_name(args.player1), bot_name(args.player2)]
    scores = []
    for i in xrange(args.count):
        # A sequential, deterministic seed is used for each match that can be
        # overridden by user provided ones.
        match_seed = str(args.game_seed) + '-' + str(i)
        if args.match_seeds and i < len(args.match_seeds):
            match_seed = args.match_seeds[i]
        result = play(players,
                      not args.headless,
                      args.animate,
                      args.play_in_thread,
                      match_seed=match_seed,
                      names=names,
                      quiet=args.quiet)
        scores.append(result)
        if args.quiet >= 3 and args.headless:
            unmute_all()
        print '{0} - seed: {1}'.format(result, match_seed)
    return scores


def task(data):
    (player1,
     player2,
     headless,
     animate,
     play_in_thread,
     match_seed,
     quiet) = data

    result = play(
        [
            make_player(player1),
            make_player(player2)
        ],
        not headless,
        animate,
        play_in_thread,
        match_seed=match_seed,
        names=[
            bot_name(player1),
            bot_name(player2)
        ],
        quiet=quiet,
    )
    if quiet >= 3 and headless:
        unmute_all()
    print '{0} - seed: {1}'.format(result, match_seed)
    return result


def test_runs_concurrently(args):
    data = []
    for i in xrange(args.count):
        match_seed = str(args.game_seed) + '-' + str(i)
        if args.match_seeds and i < len(args.match_seeds):
            match_seed = args.match_seeds[i]
        data.append([
            args.player1,
            args.player2,
            args.headless,
            args.animate,
            args.play_in_thread,
            match_seed,
            args.quiet,
        ])
    num_cpu = multiprocessing.cpu_count() - 1
    if num_cpu == 0:
        num_cpu = 1
    return multiprocessing.Pool(num_cpu).map(task, data)


def bot_name(path_to_bot):
    return os.path.splitext(os.path.basename(path_to_bot))[0]


def main():
    args = parser.parse_args()
    if args.quiet >= 3:
        mute_all()

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
