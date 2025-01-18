from typing import NewType, List
import abstraction
from abstraction import fast_cluster_prediction

VALID_ACTIONS = ["k", "bMIN", "bMAX", "c", "f"]

GameAction = NewType("GameAction", str)

class PostflopHistory:
    def __init__(self, actions: List[GameAction] = [], sample_id: int = 0):
        self.actions = actions
        self.sample_id = sample_id
        self.current_stage = actions.count("/")

    def current_player(self) -> int:
        """
        Determine the current player: -1 indicates no player (chance stage).
        """
        if len(self.actions) <= 3 or self._stage_has_ended() or self.actions[-1] == "/":
            return -1
        last_stage = self._get_last_stage()
        return (len(last_stage) + 1) % 2

    def _stage_has_ended(self) -> bool:
        """Check if the current betting stage has ended."""
        last_action = self.actions[-1]
        second_last_action = self.actions[-2] if len(self.actions) > 1 else None

        return (
            last_action == "f" or
            last_action == "c" or
            (second_last_action == "k" and last_action == "k")
        )

    def _get_last_stage(self) -> List[GameAction]:
        """Retrieve the list of actions in the most recent game stage."""
        last_stage_start = max(idx for idx, action in enumerate(self.actions) if action == "/")
        return self.actions[last_stage_start + 1 :]

    def is_chance_stage(self) -> bool:
        """Check if the current stage is a chance stage."""
        return self.current_player() == -1

    def get_infoset_key(self) -> str:
        """Generate the information set key for the current game state."""
        actions = self.actions
        player = self.current_player()
        infoset = []

        # --- Card Abstraction ---
        stage_index = 0
        player_hand = []

        # Determine player's hand
        if player == 0:
            player_hand = [actions[0][:2], actions[0][2:4]]
        else:
            player_hand = [actions[1][:2], actions[1][2:4]]

        community_cards = []

        for action in actions:
            if action not in VALID_ACTIONS:
                if action == "/":
                    stage_index += 1
                    continue

                if stage_index != 0:
                    community_cards += [action[i : i + 2] for i in range(0, len(action), 2)]

                if stage_index in {1, 2, 3}:
                    assert len(action) in {6, 2}, "Unexpected action length."
                    infoset.append(str(fast_cluster_prediction(player_hand + community_cards)))
            else:
                infoset.append(action)

        print("Hand with community cards:", player_hand + community_cards)
        return "".join(infoset)
