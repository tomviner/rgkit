import rg
import random


class Robot:
    def act(self, game):
        center = rg.CENTER_POINT
        enemy_bots = [
            b for b in game.robots.values()
            if b.player_id != self.player_id]
        target = min(
            enemy_bots,
            key=lambda bot: rg.wdist(bot.location, center)
        )

        adjacent_bots = []
        for enemy in enemy_bots:
            if rg.wdist(enemy.location, self.location) == 1:
                adjacent_bots.append(enemy)
        if len(adjacent_bots) > self.hp / 9:
            return ['suicide']
        elif adjacent_bots:
            return ['attack', min(adjacent_bots, key=lambda b: b.hp).location]

        adj = rg.locs_around(
            target.location,
            filter_out=('invalid', 'obstacle')
        )
        closest_locs = min(rg.wdist(loc, self.location) for loc in adj)
        dests = [
            loc
            for loc in adj
            if rg.wdist(loc, self.location) == closest_locs]
        dest = random.choice(dests)
        if rg.wdist(target.location, self.location) == 1:
            return ['attack', target.location]
        else:
            return ['move', rg.toward(self.location, dest)]
