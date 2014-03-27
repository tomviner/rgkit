
import unittest
from os import path
import commands


class TestAttack(unittest.TestCase):
    def test_acceptance_cli(self):
        testdir = path.dirname(__file__)

        # test if -h runs
        cmd = testdir + "/../rgkit/run.py -h"
        exit_code, ignore = commands.getstatusoutput(cmd)
        self.assertEqual(exit_code, 0)

        robot_file = testdir + "/acceptance_robot.py"
        # test simple robot
        cmd = testdir + "/../rgkit/run.py -H {0} {0}".format(robot_file)

        exit_code, out = commands.getstatusoutput(cmd)
        self.assertEqual(exit_code, 0)
