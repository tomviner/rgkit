import random

class Robot:
    def act(self, game):
        loc = self.location
        right = (loc[0] + 1, loc[1])
        left = (loc[0] - 1, loc[1])
        up = (loc[0], loc[1] + 1)
        down = (loc[0], loc[1] -1)
        new_loc = random.choice((up, down, left, right))        
        return random.choice((['move', new_loc], ['attack', new_loc]))

