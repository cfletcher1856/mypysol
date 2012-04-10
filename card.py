from ice import Ice


class Card(Ice):
    _face = {
        1: 'A',
        11: 'J',
        12: 'Q',
        13: 'K'
    }

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.img = '{0}{1}.png'.format(suit, rank)

    @property
    def color(self):
        return 'red' if self.suit in 'dh' else 'black'

    @property
    def face(self):
        return self._face.get(self.rank)
