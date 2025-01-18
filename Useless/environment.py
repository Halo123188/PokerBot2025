from playertype import PlayerType
from AIBot import CFRAIPlayer
from skeleton.states import GameState, TerminalState, RoundState

class PokerEnvironment:

    def __init__(self, input_cards=False) -> None:
        self.players = []
        self.deck = Deck() #May not use


        self.game_stage = 1  # To keep track of which phase of the game we are at, new_round is 0
        # Changes every round
        self.dealer_button_position = 0  # This button will move every round
        self.position_in_play = 0

        self.total_pot_balance = 0  # keep track of pot size of total round
        self.stage_pot_balance = 0  # keep track of pot size for current round
        self.community_cards = []  # a.k.a. the board

        self.raise_position = 0  # This is to keep track of who is the first player to have placed the highest bet, so we know when to end the round
        self.showdown = False  # flag that can be used to reveal opponents cards if needed

        # FIXED BALANCES
        self.new_player_balance = 400
        self.SMALL_BLIND = 1
        self.BIG_BLIND = 2

        self.input_cards = input_cards

        self.history = []
        self.players_balance_history = []  # List of "n" list for "n" players

        def add_player(self):
            self.players.append(PlayerType(self.new_player_balance))
        
        def get_player(self, idx) -> PlayerType:
            return self.players[idx]
        
        def add_AI_player(self):  # Add a dumb AI
            self.players.append(CFRAIPlayer(self.new_player_balance))
            self.AI_player_idx = len(self.players) - 1

        def start_new_round(self):
            for player in self.players:
                player.playing_current_round = True
                player.current_bet = 0
                player.clear_hand()
                player.player_balance = self.new_player_balance
            
            self.community_cards = []
            self.stage_pot_balance = 0
            self.total_pot_balance = 0

            self.showdown = False
            self.history = []

            self.game_stage = 1
            self.move_to_next_game_stage()

        def get_highest_current_bet(self):
            highest_bet = 0
            for player in self.players:
                if player.current_bet > highest_bet and player.playing_current_round:
                    highest_bet = player.current_bet

            return highest_bet
        
        def update_stage_pot_balance(self):
            self.stage_pot_balance = 0
            for player in self.players:
                self.stage_pot_balance += player.current_bet

        def play_current_stage(self, action: str = ""):
            self.update_stage_pot_balance()
            if self.players[self.position_in_play].is_AI:
                action = self.players[self.position_in_play].place_bet(self)

            else:  # Real player's turn
                if action == "":  # No decision has yet been made
                    return
                else:
                    action = self.players[self.position_in_play].place_bet(action, self)
                    if action is None:  # invalid action
                        return

            self.history += [action]

            if action[0] == "b":
                self.raise_position = self.position_in_play
            elif action == "f":
                self.players[self.position_in_play].playing_current_round = False  # Player has folded
            self.update_stage_pot_balance()

            
            self.move_to_next_playing_player()

            if self.position_in_play == self.raise_position:  # Everyone has called with no new raises
                self.move_to_next_game_stage()
        
        def move_to_next_playing_player(self, from_position=None):
            assert self.count_remaining_players_in_round() > 1
            if from_position is not None:
                self.position_in_play = from_position
            self.position_in_play += 1
            self.position_in_play %= len(self.players)

            while not self.players[self.position_in_play].playing_current_round:
                self.position_in_play += 1
                self.position_in_play %= len(self.players)

        def play_preflop(self, round_state, active):
            """
            About the small blind position:
            The "small blind" is placed by the player to the left of the dealer button and the "big blind" is then posted by the next player to the left.
            The one exception is when there are only two players (a "heads-up" game), when the player on the button is the small blind, and the other player is the big blind.
            """
            # Set the blind values
            # Big Blind
            self.players[((self.dealer_button_position + 1) % len(self.players))].current_bet = (
                self.BIG_BLIND
            )
            # Small Blind
            self.players[((self.dealer_button_position + 2) % len(self.players))].current_bet = (
                self.SMALL_BLIND
            )

            self.update_stage_pot_balance()

            if len(self.players) == 2:
                self.position_in_play = self.dealer_button_position
            else:
                self.position_in_play = (self.dealer_button_position + 3) % len(self.players)
            self.raise_position = self.position_in_play

            for i in range(len(self.players)):
                # First card is non-dealer, second is dealer
                player_idx = (self.dealer_button_position + 1 + i) % len(self.players)

                my_cards = round_state.hands[active]

                for i in range(2):
                    card =  my_cards[i][0] + my_cards[i][1]

                    card_str += str(card)
                    self.players[player_idx].add_card_to_hand(card)

                self.history += [card_str]  # always deal to the non-dealer first
        
