import rg
import random
import statistics

def get_offset_to_aim_for():
    x_offset = random.randint(-5, 5)
    y_offset = random.randint(-5, 5)
    return (x_offset, y_offset)

offset = get_offset_to_aim_for()
LOCATION_TO_AIM_FOR = (rg.CENTER_POINT[0] - offset[0], rg.CENTER_POINT[1] - offset[1])

class Robot:

    def act(self, game):
        # if we're in the LOCATION_TO_AIM_FOR, stay put
        if self.location == self.get_average_enemy_location(game):
            return ['guard']

        # if there are enemies around, attack them
        enemy_locations = self.get_surrounding_enemy_locations(game)
        if len(enemy_locations) >= 5:
            return ['suicide']
        elif len(enemy_locations) > 0:
            return ['attack', random.choice(enemy_locations)]

        # move toward the center
        return ['move', rg.toward(self.location, self.get_average_enemy_location(game))]

    def get_surrounding_enemy_locations(self, game):
        nearbys = []
        for loc, bot in game.robots.items():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    nearbys.append(loc)

        return nearbys

    def get_average_enemy_location(self, game):
        enemies = []
        for loc, bot in game.robots.items():
            if bot.player_id != self.player_id:
                enemies.append(loc)
        
        return (statistics.median([en[0] for en in enemies]), 
            statistics.median([en[1] for en in enemies]))
        
