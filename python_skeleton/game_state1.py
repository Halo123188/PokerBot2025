from deuces import Deck, Evaluator, Card
import random

from deuces import Deck, Evaluator, Card
import random


class BountyHoldemEnv:
    def __init__(self, rounds=1):

        self.deck = None
        self.board = []
        self.player_hands = []
        self.player_chips = [400, 400]
        self.player_bankroll = [0, 0]
        self.pot = 0
        self.current_bet = 0 #maximum bet in this stage
        self.bet = [0, 0] # how many chips each player has bet in this stage
        self.active_players = [True, True]
        self.dealer = 0
        self.big_blind = 2
        self.small_blind = 1
        self.history = []  # Logs game history
        self.action_history = []  # Logs actions for the current betting round
        self.bounties = [None, None]  # Bounty ranks
        self.evaluator = Evaluator()
        self.show_down = False
        self.is_terminal = False
        self.current_stage = "pre-flop"
        self.player = 0
        self.strong = False


    def reset_round(self):
        """
        Reset the game state for a new round.
        """
        self.deck = Deck()
        self.board = [] #Card类型
        self.player_hands = [self.deck.draw(2), self.deck.draw(2)] #Card类型
        self.player_chips = [400, 400]
        self.pot = 0
        self.current_bet = 0
        self.active_players = [True, True]
        self.action_history = []
        self.bet  = [0, 0]
        self.history = []
        self.show_down = False
        self.is_terminal = False
        self.current_stage = "pre-flop"
        self.player = 0

        self.assign_bounties()

        # Post blinds
        self.post_blinds()

        # Start pre-flop history with hands
        player1_hand = self.format_hand(self.player_hands[0])
        player2_hand = self.format_hand(self.player_hands[1])
        self.history.append(self.check_bounty_hit(0))
        self.history.append(self.check_bounty_hit(1))
        self.history.append(player1_hand)
        self.history.append(player2_hand)

    def post_blinds(self):
        """
        Posts the small and big blinds.
        """
        small_blind_player = self.dealer
        big_blind_player = (self.dealer + 1) % 2

        self.player_chips[small_blind_player] -= self.small_blind
        self.player_chips[big_blind_player] -= self.big_blind

        self.bet[small_blind_player] = self.small_blind
        self.bet[big_blind_player] = self.big_blind

        self.pot += self.small_blind + self.big_blind
        self.current_bet = self.big_blind

    def valid_action(self, player, stage):
        """
        Determines the bot's action and raise amount dynamically.
        Replace this with AI logic for more advanced decision-making.
        """

        valid_actions = ['c', 'k', 'bmin', 'bmid', 'bmax' ,'f']
        if not self.active_players[player]:
            valid_actions = ['f']
            return valid_actions # Fold if inactive

        if stage != "pre-flop":
          valid_actions.remove('bmid')

        if self.current_bet == 0 or self.bet[player] == self.current_bet:  # No bet has been made
          valid_actions.remove('f')  # Remove fold as an option
          valid_actions.remove('c')  # Remove call as an option

        elif self.bet[player] < self.current_bet:
          valid_actions.remove('k')

        if self.player_chips[player] < self.pot and 'bmid' in valid_actions:
          valid_actions.remove('bmid')

        return valid_actions

    def play_betting_round(self, stage=None):
        """
        Executes a single betting round and deals board cards for flop, turn, or river if applicable.
        """
        if stage:
            self.deal_board(stage)  # Deal board cards for the stage (flop, turn, or river)

        first_check = False
        while True:
            temp_action_history = []
            for player in range(2):
                if self.active_players[player]:
                    action, raise_amount = self.bot_action(player, stage)
                    self.step(action, player, raise_amount)

                    #只要有一方fold或者call了或者都All-in了，说明这个stage就结束了
                    if action == 'f':
                      return False

                    if self.player_chips[0] == 0 and self.player_chips[1] == 0:
                      self.show_down = True
                      return False

                    if action == 'c' and stage != "pre-flop":
                      return True

                    if action == 'c' and stage == "pre-flop":
                      if first_check:
                        return True


                    temp_action_history.append(action)
                    first_check = True

            if stage == "pre-flop":
              if temp_action_history == ['c', 'k']:
                return True
            else:
              if temp_action_history == ['k', 'k']:
                return True

    def step(self, action, player):
        """
        Handles a player's action: 'c', 'k', 'r', 'f'.
        Logs raises as 'r' regardless of the amount.
        """
        # if action not in ['c', 'k', 'bmin', 'bmid', 'bmax', 'f']:
        #     raise ValueError("Invalid action. Use 'c', 'k', 'bmin', 'bmid', 'bmax' or 'f'.")

        # Handle action logic

        raise_amount = 0
        if action == "bmin":
          if self.current_bet - self.bet[player] + 1 >= min(self.pot, self.player_chips[player]):
            raise_amount = min(self.pot, self.player_chips[player])
          else:
            raise_amount = random.randint(self.current_bet - self.bet[player] + 1, min(self.pot, self.player_chips[player]))
        elif action == "bmid":
          if self.pot >= min(2 * self.pot, self.player_chips[player]):
            raise_amount = min(2 * self.pot, self.player_chips[player])
          else:
            raise_amount = random.randint(self.pot, min(2 * self.pot, self.player_chips[player]))
        elif action == "bmax":
          if min(2 * self.pot, self.player_chips[player]) >= self.player_chips[player]:
            raise_amount = self.player_chips[player]
          else:
            raise_amount = random.randint(min(2 * self.pot, self.player_chips[player]), self.player_chips[player])

        if action == 'c':  # Call
            chips_needed = self.current_bet - self.bet[player]
            self.bet[player] = self.current_bet
            self.player_chips[player] -= chips_needed
            self.pot += chips_needed
            self.history.append(action)

        elif action == 'bmin' or action == 'bmid' or action == 'bmax':  # Raise
            # Log the raise as 'r', but apply the custom raise amount
            self.current_bet = self.bet[player] + raise_amount
            self.player_chips[player] -= raise_amount
            self.bet[player] += raise_amount
            self.pot += raise_amount
            self.history.append('b'+str(raise_amount))

        elif action == 'f':  # Fold
            self.active_players[player] = False
            self.history.append(action)

        elif action == 'k':  # Check
            self.history.append(action)


    def deal_board(self, stage):
        """
        Deals cards to the board and logs the current board state.
        """
        if stage == "flop":
            self.board.extend(self.deck.draw(3))
            self.history[0] = self.check_bounty_hit(0)
            self.history[1] = self.check_bounty_hit(1)

        elif stage in ["turn", "river"]:
            self.board.append(self.deck.draw(1))
            self.history[0] = self.check_bounty_hit(0)
            self.history[1] = self.check_bounty_hit(1)

        # Log the board
        board_str = self.format_hand(self.board)
        if stage != "pre-flop":
          self.history.append("/")
          self.history.append(board_str)

    def evaluate_winner(self):
        """
        Determines the winner of the round.
        """
        if not self.active_players[0]:
            return 1  # Player 0 folded, Player 1 wins
        if not self.active_players[1]:
            return 0  # Player 1 folded, Player 0 wins

        # Evaluate hands
        player1_score = self.evaluator.evaluate(self.board, self.player_hands[0])
        player2_score = self.evaluator.evaluate(self.board, self.player_hands[1])

        if player1_score < player2_score:
            return 0  # Player 0 wins
        elif player2_score < player1_score:
            return 1  # Player 1 wins
        else:
            return -1  # Draw

    def end_round(self):
        """
        Ends the round, evaluates the winner, and updates history with bounty results.
        """

        if self.show_down:
            if len(self.board) == 0:
              self.board.extend(self.deck.draw(3))
              self.history.append('/')
              self.history.append(self.format_hand(self.board))
              self.history[0] = self.check_bounty_hit(0)
              self.history[1] = self.check_bounty_hit(1)
            if len(self.board) == 3:
              self.board.append(self.deck.draw(1))
              self.history.append('/')
              self.history.append(self.format_hand(self.board))
              self.history[0] = self.check_bounty_hit(0)
              self.history[1] = self.check_bounty_hit(1)
            if len(self.board) == 4:
              self.board.append(self.deck.draw(1))
              self.history.append('/')
              self.history.append(self.format_hand(self.board))
              self.history[0] = self.check_bounty_hit(0)
              self.history[1] = self.check_bounty_hit(1)

        winner = self.evaluate_winner()



        # Determine bounty hits
        player_bounty_hits = [self.check_bounty_hit(0), self.check_bounty_hit(1)]
        bounty_result = f'"{player_bounty_hits[0]}", "{player_bounty_hits[1]}"'

        # Append bounty results to history
        winning = 400 - self.player_chips[1-winner]
        if self.check_bounty_hit(winner):
          winning = winning * 1.5 + 10.0
        return winning

        # Rotate dealer and reset round
        #假设不换！！！！！！可能要改！！！！！
        #self.dealer = (self.dealer + 1) % 2
    def advance_to_next_round(self):
      if self.current_stage == "pre-flop":
        self.current_stage = "flop"
      elif self.current_stage == "flop":
        self.current_stage = "turn"
      elif self.current_stage == "turn":
        self.current_stage = "river"

    def check_stage_end(self):
        """
        Advances to the next round.
        """
        if self.history[-1] == 'f':
            self.is_terminal = True
            self.active_players[self.player] = False
            return
        if self.player_chips[0] == 0 and self.player_chips[1] == 0:
            self.show_down = True
            self.is_terminal = True
            return
        if self.current_stage != "pre-flop":
          if self.history[-1] == 'c':
            self.advance_to_next_round()
            return
          if self.history[-1] == 'k' and self.history[-2] == 'k':
            self.advance_to_next_round()
            return
        else:
          if self.history[-1] == 'c' and len(self.history) > 5:
            self.advance_to_next_round()
            return
          if self.history[-1] == 'k' and self.history[-2] == 'c':
            self.advance_to_next_round()
            return


    def check_bounty_hit(self, player):
        """
        Checks if a player's bounty was hit.
        """
        bounty_rank = self.bounties[player]
        return int(any(Card.STR_RANKS[Card.get_rank_int(card)] == bounty_rank for card in self.player_hands[player] + self.board))

    def assign_bounties(self):
        """
        Assign random bounties to both players.
        """
        self.bounties = [random.choice(Card.STR_RANKS) for _ in range(2)]

    def format_hand(self, cards):
        """
        Formats a list of cards into the required shorthand format.
        """
        s = ""

        for card in cards:
          rank = Card.STR_RANKS[Card.get_rank_int(card)]
          suit_int = Card.get_suit_int(card)

          if suit_int == 1:
            suit = "s"
          elif suit_int == 2:
            suit = "h"
          elif suit_int == 4:
            suit = "d"
          elif suit_int == 8:
            suit = "c"
          s += rank + suit


        return s
    def next_player(self):
      self.player = 1 - self.player

    def play_game(self):
        """
        Plays the game for the specified number of rounds.
        """
        #如果有人fold的话，那么后面都不需要进行了
        for _ in range(self.rounds):
            self.reset_round()
            result = self.play_betting_round("pre-flop")
            self.bet = [0, 0]
            self.current_bet = 0

            if result == True:
              result = self.play_betting_round("flop")
              self.bet = [0, 0]
              self.current_bet = 0

            if result == True:
              result = self.play_betting_round("turn")
              self.bet = [0, 0]
              self.current_bet = 0

            if result == True:
              result = self.play_betting_round("river")
              self.bet = [0, 0]
              self.current_bet = 0

            self.end_round(result)

            # Print results
            for entry in self.history:
              print(entry)

class GameState:
    def __init__(self):
        self.current_stage = "pre-flop"

    def get_preflop_infoset(self, history, player):
        """
        Returns the information set for the given player.
        Encodes private and public information.
        :param
            history: all cards and actions for a round.
            bb: true if the current bot is big blind
        :return: String representation of the information set.

        'AsAh
        """
        ##如果是big blind的话
        if player == 1:
            cards = str(history[1]) + str(history[3])
        else:
            cards = str(history[0]) + str(history[2])

        actions = history[4:]
        abstracted_action = self.get_preflop_cluster_id(actions)

        strong = False
        for action in actions:
            if action == "bmin" or action == "bmid" or action == "bmax":
                strong = True

        infoset = cards + abstracted_action

        return infoset, strong

    def get_postflop_infoset(self, history, strong, current_stage, player):

        if player == 1:
            cards = str(history[1]) + str(history[3])
        else:
            cards = str(history[0]) + str(history[2])

        if current_stage == "flop":
            actions = history[4:]
            flop = False
            all_abstracted_action = ""
            current_round = []
            for index in range(len(actions)):
                if actions[index] == "/":
                    flop = True
                    cards += actions[index + 1]
                elif flop and actions[index - 1] == "/":
                    continue
                elif flop:
                    current_round.append(actions[index])

            if current_round:
                abstracted_action = self.predict_cluster(current_round)

            infoset = cards + str(strong) + abstracted_action
        elif current_stage == "turn" or current_stage == "river":
            actions = history[4:]
            all_abstracted_action = ""

            # Process only the current round and the previous round
            rounds = []  # List to store actions for each round
            current_round = []

            found_card = False

            # Loop backward through the actions to collect the last two rounds
            for index in range(len(actions) - 1, -1, -1):
                if actions[index] == "/":  # A round ends at "/"
                    if current_round:
                        rounds.append(current_round[::-1])  # Reverse to maintain original order
                        current_round = []
                    if len(rounds) == 2:  # Stop once we have the last two rounds
                        break
                elif not found_card and len(actions[index]) >= 2 and actions[index][1] in ['s', 'h', 'd', 'c']: #added this
                    cards += actions[index]
                    found_card = True
                elif found_card and len(actions[index]) >= 2 and actions[index][1] in ['s', 'h', 'd', 'c']:
                   continue
                else:
                    current_round.append(actions[index])

            ##以下需要修改
            if current_round:  # Add the last remaining round (if any)
                rounds.append(current_round[::-1])

            # Process the last two rounds (if available)
            for round_actions in reversed(rounds):  # Reverse again to process rounds in order
                abstracted_action = self.predict_cluster(round_actions)
                all_abstracted_action += abstracted_action + "/"

            if history[-1] != '/' and all_abstracted_action[-1] == '/': #added this
                all_abstracted_action = all_abstracted_action[:-1] #added this

            infoset = cards + str(int(strong)) + all_abstracted_action

        return infoset

    def get_preflop_cluster_id(self, actions):
        return "".join(actions) if actions else "(None)"

    def predict_cluster(self, actions):
        return "".join(actions) if actions else "(None)"
