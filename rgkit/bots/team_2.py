from rgkit import rg
import random

class Robot:
    def __init__(self):
        self.prev_locations = {}

    def act(self, game):
        # if we're in the center, stay put
        if self.location == rg.CENTER_POINT:
            return ['guard']

        # if there are enemies around, attack them
        for loc, bot in game.robots.items():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    return ['attack', loc]

                anticipated_loc = rg.toward(loc, rg.CENTER_POINT)
                if rg.dist(anticipated_loc, self.location) <= 1:
                    return ['attack', anticipated_loc]

        # move toward the center
        return ['move', rg.toward(self.location, rg.CENTER_POINT)]
