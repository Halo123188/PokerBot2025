from typing import NewType, List
import abstraction
from abstraction import predict_cluster

DISCRETE_ACTIONS = ["k", "bMIN", "bMAX", "c", "f"]

Action = NewType("Action", str)

class PostflopHistory():

    def __init__(self, history: List[Action] = [], sample_id=0):
        self.history = history
        self.sample_id = sample_id
        self.stage_i = history.count("/")

    def player(self):
        """
        # non dealer, dealer
        1. ['AkTh', 'QdKd', '/', 'Qh', 'b2', 'c', '/', '2d', b2', 'f']
        """
        if len(self.history) <= 3:
            return -1
        elif self._game_stage_ended():
            return -1
        elif self.history[-1] == "/":
            return -1
        else:
            last_game_stage = self.get_last_game_stage()
            # latest game stage
            return (len(last_game_stage) + 1) % 2

    def _game_stage_ended(self):
        last_action = self.history[-1]
        opp_action = self.history[-2]

        if last_action == "f":
            return True
        elif last_action == "c":
            return True
        elif opp_action == "k" and last_action == "k":
            return True
        else:
            return False

    def get_last_game_stage(self):
        last_game_stage_start_idx = max(loc for loc, val in enumerate(self.history) if val == "/")
        last_game_stage = self.history[last_game_stage_start_idx + 1 :]
        return last_game_stage

    def is_chance(self):
        return self.player() == -1

    def get_infoSet_key_online(self) -> List[Action]:
        history = self.history
        player = self.player()
        infoset = []
        # ------- CARD ABSTRACTION -------
        # Assign cluster ID for FLOP/TURN/RIVER
        stage_i = 0
        hand = []
        if player == 0:
            hand = [history[0][:2], history[0][2:4]]
        else:
            hand = [history[1][:2], history[1][2:4]]
        community_cards = []
        for i, action in enumerate(history):
            if action not in DISCRETE_ACTIONS:
                if action == "/":
                    stage_i += 1
                    continue
                if stage_i != 0:
                    community_cards += [history[i][j : j + 2] for j in range(0, len(action), 2)]
                if stage_i == 1:
                    assert len(action) == 6
                    infoset.append(str(predict_cluster(hand + community_cards)))
                elif stage_i == 2:
                    assert len(action) == 2
                    infoset.append(str(predict_cluster(hand + community_cards)))
                elif stage_i == 3:
                    assert len(action) == 2
                    infoset.append(str(predict_cluster(hand + community_cards)))
            else:
                infoset.append(action)

        print("my hand with community cards: ", hand + community_cards)
        return "".join(infoset)
