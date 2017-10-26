#!/usr/bin/env python

import rg
import random

class Robot:
    def random_location(self):
        return random.choice(rg.locs_around(self.location, filter_out=['obstacle']))

    def friendly_bots_locs(self):
        return rg.robots['location']

    def enemy_bot_locations(self, game):
        return [pt for pt, robot in game.robots.items() if robot.player_id != self.player_id]

    def act(self, game):
        # if we're in the center, stay put
        if self.location == rg.CENTER_POINT:
            return ['guard']

        num_enemies_near = sum([ pt in self.enemy_bot_locations(game) for pt in rg.locs_around(self.location)])
        if num_enemies_near > 1 and self.hp < 20:
            return ['suicide']

        # if there are enemies around, attack them
        for loc, bot in game.robots.items():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    return ['attack', loc]

        # move toward the center
        dist_to_center = rg.wdist(self.location, rg.CENTER_POINT)
        if dist_to_center > 5:
            next_location = rg.toward(self.location, rg.CENTER_POINT)
        else:
            next_location = self.random_location()
        
        if next_location in game.robots:
            return ['guard']

        return ['move', next_location]




