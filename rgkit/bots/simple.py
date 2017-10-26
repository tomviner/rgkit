import rg

class Robot(object):
    def act(self, game):
        return ['move', rg.toward(self.location, rg.CENTER_POINT)]
