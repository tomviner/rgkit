import rg
import random

class Robot(object):
    def act(self, game):

        target = [0, 0]
        for i in (0, 1):
            target[i] += rg.CENTER_POINT[i] + random.randint(-4, 2)

        return ['move', rg.toward(self.location, target)]
