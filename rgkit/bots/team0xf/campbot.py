import rg

class Robot:
    def act(self, game):
        mybots = [bot for bot in game.robots.values()
                  if bot['player_id'] == self.player_id]
        if 'spawn' in rg.loc_types(self.location):
            return ['move', rg.toward(self.location,rg.CENTER_POINT)]
        
        my_friendly_neighbours = [ bot for bot in game.robots.values()
            if bot['player_id'] == self.player_id
                and 'spawn' in rg.loc_types(bot.location)
                and bot.location in rg.locs_around(self.location)]
        if my_friendly_neighbours:
            return ['move', rg.toward(self.location,rg.CENTER_POINT)]
        return ['guard']
