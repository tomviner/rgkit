class Robot:
    def act(self, game):
        neighbour_loc = [
                (self.location[0] - 1, self.location[1] - 1),
                (self.location[0] - 1, self.location[1] + 1),
                (self.location[0] + 1, self.location[1] - 1),
                (self.location[0] + 1, self.location[1] + 1)
        ]

        for n in neighbour_loc:
            if n not in game['robots']:
                # neighbour location is empty
                is_surrounded = False
                break
            else:
                # n is not empty
                is_surrounded = game['robots'][n].player_id == self.player_id
                break
        else:
            is_surrounded = True

        if is_surrounded:
            return ['suicide']



        else:
            return ['guard']
