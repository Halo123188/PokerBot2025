import abstraction
from typing import List
from abstraction import (
    get_preflop_cluster_id,
)
from typing import NewType, List

DISCRETE_ACTIONS = ["k", "bMIN", "bMID", "bMAX", "c", "f"]

Action = NewType("Action", str)

class PreflopHistory():

    def __init__(self, history: List[Action] = [], sample_id = 0):
        self.history = history
        self.sample_id = sample_id

    def is_terminal(self):
        num_round = len(self.history)
        street = len(self.history[-1])

        return num_round > 0 and street == 10

    def player(self):
        """
        1. ['AkTh', 'QdKd', 'bMID', 'c', '/', 'Qh2d3s4h5s']
        """
        if len(self.history) < 2:
            return -1
        elif self._game_stage_ended():
            return -1
        elif self.history[-1] == "/":
            return -1
        else:
            return (len(self.history) + 1) % 2

    def _game_stage_ended(self):
        last_action = self.history[-1]
        opp_action = self.history[-2]

        if last_action == "f":
            return True
        elif last_action == "c" and len(self.history) > 3:
            return True
        elif opp_action == "c" and last_action == "k":
            return True
        else:
            return False

    def is_chance(self):
        return self.player() == -1

    def get_infoSet_key(self) -> List[Action]:
        """
        Abstract cards and bet sizes
        """

        if self.is_chance() or self.is_terminal():
            raise Exception

        infoset = []
        cluster_id = str(get_preflop_cluster_id(self.history[self.player()]))

        # ------- CARD ABSTRACTION -------
        infoset.append(cluster_id)

        for action in self.history:
            if action in DISCRETE_ACTIONS:
                infoset.append(action)

        return infoset
