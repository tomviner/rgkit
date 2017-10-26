import rg



class Robot:
    def act(self, game):
        center = rg.CENTER_POINT
        enemy_bots = [b for b in game.robots.values() if b.player_id != self.player_id]
        target = min(enemy_bots, key=lambda bot: rg.wdist(bot.location, center))
        for enemy in enemy_bots:
            if rg.wdist(enemy.location, self.location) == 1:
                return ['attack', enemy.location]
        adj = rg.locs_around(target.location, filter_out=('invalid', 'obstacle'))
        dest = min(adj, key=lambda loc: rg.wdist(loc, self.location))
        if rg.wdist(target.location, self.location) > 1:
            return ['move', rg.toward(self.location, dest)]
        else:
            return ['attack', target.location]
