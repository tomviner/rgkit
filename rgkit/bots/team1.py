import random
import rg

THRES = 5

class Robot:
    def __init__(self):
        self.turn_count = 0

    def check_for_enemies(self, game):
        bots = []
        for loc, bot in game.get('robots').items():
          if bot.player_id != self.player_id:
            bots.append(loc)

        return bots

    def act(self, game):
        self.turn_count += 1
        print(self.check_for_enemies(game))

        if self.turn_count == 1:
            return ['move', rg.toward(self.location, rg.CENTER_POINT)]

        enemy_locs = self.check_for_enemies(game)
        adj_locs = rg.locs_around(self.location)

        # check location and be aggresive
        for loc in adj_locs:
            if loc in enemy_locs:
                if self.hp < THRES:
                    return ['suicide']
                return ['attack', loc]

        # if at centre, defend
        if self.location == rg.CENTER_POINT:
            return ['guard']

        # default move to centre
        return ['move', rg.toward(self.location, rg.CENTER_POINT)]

