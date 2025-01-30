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

    def bot_action(self, player, stage):
        """
        Determines the bot's action and raise amount dynamically.
        Replace this with AI logic for more advanced decision-making.
        """
        if not self.active_players[player]:
            return 'f', 0  # Fold if inactive

        # Need to change!!! into raise or bet
        # bmin -> pot size;  bmid -> 2 * pot size;  bmax -> all in

        valid_actions = ['c', 'k', 'bmin', 'bmid', 'bmax' ,'f']

        if stage != "pre-flop":
          valid_actions.remove('bmid')

        if self.current_bet == 0 or self.bet[player] == self.current_bet:  # No bet has been made
          valid_actions.remove('f')  # Remove fold as an option
          valid_actions.remove('c')  # Remove call as an option

        elif self.bet[player] < self.current_bet:
          valid_actions.remove('k')

        if self.player_chips[player] < self.pot and 'bmid' in valid_actions:
          valid_actions.remove('bmid')

        action = random.choice(valid_actions) #need to be changed

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

        return action, raise_amount

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

    def step(self, action, player, raise_amount): #added raise_amount
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
        abstracted_card = get_preflop_card_id(cards)
        abstracted_action = get_preflop_action_id(actions, player)

        strong = False
        for action in actions:
            if action[0] == "b":
                strong = True

        infoset = abstracted_card + abstracted_action

        return infoset, strong
  def get_postflop_infoset(self, history, strong, current_stage, player, pot):
        hit_bounty = ""
        cards = []
        if player == 1:
            hit_bounty = str(history[1])
            card1 = str(history[3][0]) + str(history[3][1])
            card2 = str(history[3][2]) + str(history[3][3])
            cards.append(Card.new(card1))
            cards.append(Card.new(card2))
        else:
            hit_bounty = str(history[0])
            card1 = str(history[2][0]) + str(history[2][1])
            card2 = str(history[2][2]) + str(history[2][3])
            cards.append(Card.new(card1))
            cards.append(Card.new(card2))

        all_abstracted_action = ""

        if current_stage == "flop":
            actions = history[4:]
            flop = False
            all_abstracted_action = ""
            current_round = []
            for index in range(len(actions)):
                if actions[index] == "/":
                    flop = True
                    public_card1 = str(actions[index + 1][0]) + str(actions[index + 1][1])
                    public_card2 = str(actions[index + 1][2]) + str(actions[index + 1][3])
                    public_card3 = str(actions[index + 1][4]) + str(actions[index + 1][5])
                    cards.append(Card.new(public_card1))
                    cards.append(Card.new(public_card2))
                    cards.append(Card.new(public_card3))
                elif flop and actions[index - 1] == "/":
                    continue
                elif flop:
                    current_round.append(actions[index])

            if current_round:
                all_abstracted_action = get_preflop_action_id(current_round, player, pot)

            abstraction_cards = predict_cluster(cards)
            infoset = hit_bounty + str(abstraction_cards) + str(int(strong)) + abstracted_action

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

                    public_card_history = actions[index]
                    if (len(public_card_history) == 8):
                      public_card1 = str(public_card_history[0]) + str(public_card_history[1])
                      public_card2 = str(public_card_history[2]) + str(public_card_history[3])
                      public_card3 = str(public_card_history[4]) + str(public_card_history[5])
                      public_card4 = str(public_card_history[6]) + str(public_card_history[7])
                      cards.append(Card.new(public_card1))
                      cards.append(Card.new(public_card2))
                      cards.append(Card.new(public_card3))
                      cards.append(Card.new(public_card4))
                    else:
                      public_card1 = str(public_card_history[0]) + str(public_card_history[1])
                      public_card2 = str(public_card_history[2]) + str(public_card_history[3])
                      public_card3 = str(public_card_history[4]) + str(public_card_history[5])
                      public_card4 = str(public_card_history[6]) + str(public_card_history[7])
                      public_card5 = str(public_card_history[8]) + str(public_card_history[9])
                      cards.append(public_card1)
                      cards.append(public_card2)
                      cards.append(public_card3)
                      cards.append(public_card4)
                      cards.append(public_card5)

                    found_card = True
                elif found_card and len(actions[index]) >= 2 and actions[index][1] in ['s', 'h', 'd', 'c']:
                   continue
                else:
                    current_round.append(actions[index])

            if current_round:  # Add the last remaining round (if any)
                rounds.append(current_round[::-1])

            # Process the last two rounds (if available)
            for round_actions in reversed(rounds):  # Reverse again to process rounds in order
                abstracted_action = get_postflop_action_id(round_actions, player, pot)
                all_abstracted_action += abstracted_action + "/"

            if history[-1] != '/' and all_abstracted_action[-1] == '/': #added this
                all_abstracted_action = all_abstracted_action[:-1] #added this

            abstraction_cards = predict_cluster(cards)
            infoset = hit_bounty + str(abstraction_cards) + str(int(strong)) + all_abstracted_action
        return infoset

#Abstraction
from deuces import Deck, Card, Evaluator
import time

#modify to whatever amt u want
NUM_FLOP_CLUSTERS = 10
NUM_TURN_CLUSTERS = 10
NUM_RIVER_CLUSTERS = 10
DECK = Deck.GetFullDeck()
for card in DECK:
    DECK[DECK.index(card)] = Card.int_to_str(card)

# we alr have a function in gamestate called evaluate winner that does smth different, might cause an issue
def evaluate_winner(board, player_hand, opponent_hand):
    p1_score = Evaluator.evaluate(board, player_hand)
    p2_score = Evaluator.evaluate(board, opponent_hand)
    if p1_score < p2_score:
        return 1
    elif p1_score > p2_score:
        return -1
    else:
        return 0


def get_preflop_card_id(card_history):
    bounty_id = card_history[0]
    cards = card_history[1:]

    card1_rank = cards[0]
    card2_rank = cards[2]
    card1_suit = cards[1]
    card2_suit = cards[3]

    id = card1_rank + card2_rank
    cluster_id = None

    if card1_rank == card2_rank:
      cluster_id = Adict[id]
    elif card1_suit == card2_suit:
      cluster_id = suitDict[id]
    else:
      cluster_id = unsuitDict[id]

    return cluster_id



# Abstraction based on Jenny's clusters
def get_preflop_action_id(actions, player):
    action_id = ""
    small_blind_bet = 0
    big_blind_bet = 0
    pot = 3

    prebet = ""
    abstracted_bet = ""
    postbet = ""
    small_blind_abstracted = ""
    big_blind_abstracted = ""

    start_bet = False
    for i in range(len(actions)):
      action = actions[i]
      if start_bet == False and (action == "c" or action == "f" or action == "k"):
        prebet += action
      if start_bet == True and (action == "c" or action == "f" or action == "k"):
        postbet += action
      if action[0] == "b":
        start_bet = True
        if i % 2 == 0:
          small_blind_bet += int(action[1:])
        else:
          big_blind_bet += int(action[1:])

    if small_blind_bet == 0:
      pass
    elif small_blind_bet <= pot:
      small_blind_abstracted = "bmin"
    elif small_blind_bet <= 2 * pot:
      small_blind_abstracted = "bmid"
    else:
      small_blind_abstracted = "bmax"

    if big_blind_bet == 0:
      pass
    elif big_blind_bet <= pot:
      big_blind_abstracted = "bmin"
    elif big_blind_bet <= 2 * pot:
      big_blind_abstracted = "bmid"
    else:
      big_blind_abstracted = "bmax"

    if player == 0:
      abstracted_bet = small_blind_abstracted + big_blind_abstracted
    else:
      abstracted_bet = big_blind_abstracted + small_blind_abstracted

    action_id = prebet + abstracted_bet + postbet

    return action_id

# calculates equity using Monte Carlo sampling
def calculate_equity(player_cards, community_cards=[], n=1000, timer=False):
    if timer:
        start_time = time.time()
    wins = 0
    evaluator = Evaluator()

    deck = Deck.GetFullDeck()
    player_cards = [Card.new(c) if isinstance(c, str) else c for c in player_cards]
    community_cards = [Card.new(c) if isinstance(c, str) else c for c in community_cards]

    excluded_cards = player_cards + community_cards
    for card in excluded_cards:
      deck.remove(card)

    for _ in range(n):
        random.shuffle(deck)
        opponent_cards = deck[:2]  # To avoid creating redundant copies
        community_cards_extended = community_cards.copy()
        if len(community_cards_extended) != 5:
            community_cards_extended.extend(deck[3 : 3 + (5 - len(community_cards))])

        opponent_cards = [Card.new(c) if isinstance(c, str) else c for c in opponent_cards]


        player_score = evaluator.evaluate(
            community_cards_extended, player_cards
        )
        opponent_score = evaluator.evaluate(
            community_cards_extended, opponent_cards
        )
        if player_score < opponent_score:
            wins += 1
        elif player_score == opponent_score:
            wins += 1

    if timer:
        print("Time it takes to call function: {}s".format(time.time() - start_time))

    return wins / n

# predicts the cluster using calculate_equity
def predict_cluster_fast(cards, n=1000, total_clusters=10):
    assert type(cards) == list
    equity = calculate_equity(cards[:2], cards[2:], n=n)
    cluster = min(total_clusters - 1, int(equity * total_clusters))
    return cluster

# predicts_cluster post-flop. only use the fast method cuz it improves runtime, cuz using kmeans is too slow
def predict_cluster(cards):
    assert type(cards) == list
    if len(cards) == 5:  # flop
        return predict_cluster_fast(cards, total_clusters=NUM_FLOP_CLUSTERS)
    elif len(cards) == 6:  # turn
        return predict_cluster_fast(cards, total_clusters=NUM_TURN_CLUSTERS)
    elif len(cards) == 7:  # river
        return predict_cluster_fast(cards, total_clusters=NUM_RIVER_CLUSTERS)
    else:
        raise ValueError("Invalid number of cards: ", len(cards))

def get_postflop_action_id(actions, player, pot):
    action_id = ""
    small_blind_bet = 0
    big_blind_bet = 0

    prebet = ""
    abstracted_bet = ""
    postbet = ""
    small_blind_abstracted = ""
    big_blind_abstracted = ""

    start_bet = False
    for i in range(len(actions)):
      action = actions[i]
      if start_bet == False and (action == "c" or action == "f" or action == "k"):
        prebet += action
      if start_bet == True and (action == "c" or action == "f" or action == "k"):
        postbet += action
      if action[0] == "b":
        start_bet = True
        if i % 2 == 0:
          small_blind_bet += int(action[1:])
        else:
          big_blind_bet += int(action[1:])

    if small_blind_bet == 0:
      pass
    elif small_blind_bet <= pot:
      small_blind_abstracted = "bmin"
    else:
      small_blind_abstracted = "bmax"

    if big_blind_bet == 0:
      pass
    elif big_blind_bet <= pot:
      big_blind_abstracted = "bmin"
    else:
      big_blind_abstracted = "bmax"

    if player == 0:
      abstracted_bet = small_blind_abstracted + big_blind_abstracted
    else:
      abstracted_bet = big_blind_abstracted + small_blind_abstracted

    action_id = prebet + abstracted_bet + postbet

    return action_id

Adict = {
    "AA": "1",
    "KK": "1",
    "QQ": "2",
    "JJ": "2",
    "TT": "3",
    "99": "3",
    "88": "4",
    "77": "5",
    "66": "6",
    "55": "9",
    "44": "14",
    "33": "19",
    "22": "26",
}


suitDict = {
    "AK": "4",
    "KA": "4",
    "AQ": "5",
    "QA": "5",
    "AJ": "5",
    "JA": "5",
    "AT": "6",
    "TA": "6",
    "A9": "7",
    "9A": "7",
    "A8": "8",
    "8A": "8",
    "A7": "9",
    "7A": "9",
    "A6": "10",
    "6A": "10",
    "A5": "10",
    "5A": "10",
    "A4": "11",
    "4A": "11",
    "A3": "12",
    "3A": "12",
    "A2": "14",
    "2A": "14",

    "KQ": "6",
    "QK": "6",
    "KJ": "7",
    "JK": "7",
    "KT": "8",
    "TK": "8",
    "K9": "10",
    "9K": "10",
    "K8": "12",
    "8K": "12",
    "K7": "13",
    "7K": "13",
    "K6": "15",
    "6K": "15",
    "K5": "16",
    "5K": "16",
    "K4": "17",
    "4K": "17",
    "K3": "18",
    "3K": "18",
    "K2": "20",
    "2K": "20",

    "QJ": "9",
    "JQ": "9",
    "QT": "11",
    "TQ": "11",
    "Q9": "13",
    "9Q": "13",
    "Q8": "16",
    "8Q": "16",
    "Q7": "18",
    "7Q": "18",
    "Q6": "19",
    "6Q": "19",
    "Q5": "21",
    "5Q": "21",
    "Q4": "22",
    "4Q": "22",
    "Q3": "24",
    "3Q": "25",
    "Q2": "26",
    "2Q": "26",

    "JT": "13",
    "TJ": "13",
    "J9": "16",
    "9J": "16",
    "J8": "18",
    "8J": "18",
    "J7": "21",
    "7J": "21",
    "J6": "25",
    "6J": "25",
    "J5": "27",
    "5J": "27",
    "J4": "28",
    "4J": "28",
    "J3": "29",
    "3J": "29",
    "J2": "30",
    "2J": "30",

    "T9": "18",
    "9T": "18",
    "T8": "21",
    "8T": "21",
    "T7": "25",
    "7T": "25",
    "T6": "28",
    "6T": "28",
    "T5": "30",
    "5T": "30",
    "T4": "31",
    "4T": "31",
    "T3": "32",
    "3T": "32",
    "T2": "33",
    "2T": "33",

    "98": "25",
    "89": "25",
    "97": "28",
    "79": "28",
    "96": "30",
    "69": "30",
    "95": "32",
    "59": "32",
    "94": "34",
    "49": "34",
    "93": "35",
    "39": "35",
    "92": "36",
    "29": "36",

    "87": "29",
    "78": "29",
    "86": "31",
    "68": "31",
    "85": "33",
    "58": "33",
    "84": "35",
    "48": "35",
    "83": "37",
    "38": "37",
    "82": "38",
    "28": "38",

    "76": "32",
    "67": "32",
    "75": "34",
    "57": "34",
    "74": "36",
    "47": "36",
    "73": "38",
    "37": "38",
    "72": "40",
    "27": "40",

    "65": "35",
    "56": "35",
    "64": "37",
    "46": "37",
    "63": "38",
    "36": "38",
    "62": "40",
    "26": "40",

    "54": "37",
    "45": "37",
    "53": "38",
    "35": "38",
    "52": "40",
    "25": "40",

    "43": "39",
    "34": "39",
    "42": "41",
    "24": "41",

    "32": "41",
    "23": "41",
}


unsuitDict = {
    "AK": "5",
    "KA": "5",
    "AQ": "6",
    "QA": "6",
    "AJ": "6",
    "JA": "6",
    "AT": "7",
    "TA": "7",
    "A9": "9",
    "9A": "9",
    "A8": "10",
    "8A": "10",
    "A7": "11",
    "7A": "11",
    "A6": "13",
    "6A": "13",
    "A5": "13",
    "5A": "13",
    "A4": "15",
    "4A": "15",
    "A3": "16",
    "3A": "16",
    "A2": "17",
    "2A": "17",

    "KQ": "8",
    "QK": "8",
    "KJ": "9",
    "JK": "9",
    "KT": "10",
    "TK": "10",
    "K9": "13",
    "9K": "13",
    "K8": "16",
    "8K": "16",
    "K7": "17",
    "7K": "17",
    "K6": "18",
    "6K": "18",
    "K5": "20",
    "5K": "20",
    "K4": "21",
    "4K": "21",
    "K3": "23",
    "3K": "23",
    "K2": "25",
    "2K": "25",

    "QJ": "12",
    "JQ": "12",
    "QT": "14",
    "TQ": "14",
    "Q9": "17",
    "9Q": "17",
    "Q8": "19",
    "8Q": "19",
    "Q7": "22",
    "7Q": "22",
    "Q6": "24",
    "6Q": "24",
    "Q5": "26",
    "5Q": "26",
    "Q4": "28",
    "4Q": "28",
    "Q3": "29",
    "3Q": "29",
    "Q2": "30",
    "2Q": "30",

    "JT": "17",
    "TJ": "17",
    "J9": "20",
    "9J": "20",
    "J8": "23",
    "8J": "23",
    "J7": "27",
    "7J": "27",
    "J6": "29",
    "6J": "29",
    "J5": "30",
    "5J": "30",
    "J4": "31",
    "4J": "31",
    "J3": "32",
    "3J": "32",
    "J2": "33",
    "2J": "33",

    "T9": "23",
    "9T": "23",
    "T8": "27",
    "8T": "27",
    "T7": "29",
    "7T": "29",
    "T6": "31",
    "6T": "31",
    "T5": "33",
    "5T": "33",
    "T4": "34",
    "4T": "34",
    "T3": "35",
    "3T": "35",
    "T2": "36",
    "2T": "36",

    "98": "29",
    "89": "29",
    "97": "31",
    "79": "31",
    "96": "33",
    "69": "33",
    "95": "35",
    "59": "35",
    "94": "37",
    "49": "37",
    "93": "38",
    "39": "38",
    "92": "39",
    "29": "39",

    "87": "32",
    "78": "32",
    "86": "35",
    "68": "35",
    "85": "37",
    "58": "37",
    "84": "39",
    "48": "39",
    "83": "40",
    "38": "40",
    "82": "41",
    "28": "41",

    "76": "36",
    "67": "36",
    "75": "37",
    "57": "37",
    "74": "39",
    "47": "39",
    "73": "41",
    "37": "41",
    "72": "42",
    "27": "42",

    "65": "38",
    "56": "38",
    "64": "40",
    "46": "40",
    "63": "41",
    "36": "41",
    "62": "42",
    "26": "42",

    "54": "40",
    "45": "40",
    "53": "41",
    "35": "41",
    "52": "42",
    "25": "42",

    "43": "42",
    "34": "42",
    "42": "42",
    "24": "42",

    "32": "42",
    "23": "42",
}


def test_game_state():
    game = GameState()

    history_preflop = [1, 0, '8dAs', 'Ah5h', 'b6', 'b8', 'b15', 'c']
    history_postflop = [1, 0, '8dAs', 'Ah5h', 'b6', 'b8', 'b15', 'c', '/', 'Th5s5d', 'k', 'b17', 'c', '/', 'Th5s5d4s', "k"]

    infoset, strong = game.get_preflop_infoset(history_preflop, player=0)
    print(f"Preflop Infoset: {infoset}, Strong: {strong}")

    current_stage = "turn"
    pot = 78
    infoset = game.get_postflop_infoset(history_postflop, strong, current_stage, 0, pot)
    print(f"Postflop Infoset: {infoset}")

if __name__ == "__main__":
    test_game_state()
