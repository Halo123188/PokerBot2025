# File: game_state.py
import random

SBaction = ['cbmin', 'cbmid', 'cbmax', 'cbminbmid', 'cbminbmax', 'cbminbmin', 'cbmidbmin', 'cbmidbmid', 'cbmidbmax',
            'cbmaxbmin', 'cbmaxbmid', 'cbmaxbmax', 'bminbmid', 'bminbmax', 'bminbmin', 'bmidbmin', 'bmidbmid', 'bmidbmax',
            'bmaxbmin', 'bmaxbmid', 'bmaxbmax']

BBaction = ['c', 'cbminbmid', 'cbminbmax', 'cbminbmin', 'cbmidbmin', 'cbmidbmid', 'cbmidbmax', 'cbmaxbmin', 'cbmaxbmid',
            'cbmaxbmax', "bmin", "bmid", "bmax", 'bminbmid', 'bminbmax', 'bminbmin', 'bmidbmin', 'bmidbmid', 'bmidbmax',
            'bmaxbmin', 'bmaxbmid', 'bmaxbmax']

class GameState:
    """
    Represents the state of a Texas Hold'em game.
    Tracks player hands, community cards, actions, bets, and overall game progress.
    """
    def __init__(self, ):
        self.bounty = 0 # 0: not hitting bounty; 1: hitting bounty
        self.deck = []  # The deck will be initialized externally
        self.player_hands = [[], []]  # Each player's private cards
        self.community_cards = []  # Cards on the board (flop, turn, river)
        self.action = []
        self.bets =   # Bets placed by each player in the current round
        self.total_pot = 0  # Total chips in the pot
        self.history = []  # Action history (e.g., ["P1:bet", "P2:fold"])
        self.street = 0  # Game stages: 0 = pre-flop; 3 = flop; 4 = turn; 5 = river

    def get_community_card(self):


    # --- Utility Methods ---
    def get_history_set(self):
        """
        history = ['AsAh', 'TsTh', 'c', 'bmin', 'c', '/', '3h]
        """
        self.history = self.history.append(self.player_hands)

        for actions in self.action:
            if actions == "/":
                self.history = self.history.append(self.community_cards)

        return

    def get_information_set(self, player_id):
        """
        Returns the information set for the given player.
        Encodes private and public information.
        :param player_id: ID of the player.
        :return: String representation of the information set.
        """
        private_info = ''.join(self.player_hands[player_id])
        public_info = ''.join(self.community_cards)
        bet_info = '-'.join(map(str, self.round_bets))
        return f"{private_info}:{public_info}:{bet_info}"
