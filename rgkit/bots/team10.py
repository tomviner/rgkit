import random
import rg

centre = 9, 9

class Robot:
    def act(self, game):
        loc = self.location
        right = (loc[0] + 1, loc[1])
        left = (loc[0] - 1, loc[1])
        up = (loc[0], loc[1] + 1)
        down = (loc[0], loc[1] -1)
        directions = [left, right, up, down]
        ok_directions = list(filter(safe, directions))
        new_loc = random.choice(ok_directions)        
        return random.choice((['move', new_loc], ['attack', new_loc]))

def safe(location):
   types = rg.loc_types(location)
   print(location, types)
   return 'obstacle' not in set(types)

   
