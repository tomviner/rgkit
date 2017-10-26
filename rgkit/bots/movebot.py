import random
from rgkit import rg


class Robot:
    def act(self, game):
        """Return an action possibly with params.

        ['move', (x, y)]
        ['attack', (x, y)]
        ['guard']
        ['suicide']

        Every robot, including self, has the following properties exposed:
        location — the robot's location as a tuple (x, y)
        hp — the robot's health as an int
        player_id — the robot's player_id (what "team" it belongs to)
        robot_id — a unique number identifying each robot (only available
            for robots on your team)
        """
        # if there are enemies around, attack them
        print(game)
        mv = random.choice('mmmaaaaaagggs')
        if mv == 'a':
            for loc, bot in list(game.robots.items()):
                if bot.player_id != self.player_id:
                    if rg.dist(loc, self.location) <= 1:
                        return ['attack', loc]
        if mv == 'm':
            return ['move', rg.toward(self.location, rg.CENTER_POINT)]

        if mv == 's':
            return ['suicide']

        return ['guard']
