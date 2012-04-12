class GameState(object):
    def __init__(self):
        self.foundations = {
            1: [],
            2: [],
            3: [],
            4: []
        }

        self.stock = None
        self.waste = []

        self.tableaus = {
            1: [],
            2: [],
            3: [],
            4: [],
            5: [],
            6: [],
            7: []
        }


refs = GameState()
