from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
from AIBot import CFRAIPlayer

CARD_SUITS_DICT = {"Clubs": 0, "Diamonds": 1, "Hearts": 2, "Spades": 3}
INVERSE_RANK_KEY = {
    14: "A",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "T",
    11: "J",
    12: "Q",
    13: "K",
}

class Card:
    """
    You can initialize cards two ways:
    - (RECOMMENDED) Card("Ah")
    - Card(10, "Spades")

    """

    # Immutable after it has been initialized
    def __init__(self, rank=14, suit="Spades") -> None:

        
        self.__rank = rank
        self.__suit = suit

    @property
    def rank(self):
        return self.__rank

    @property
    def suit(self):
        return self.__suit

    @property
    def idx(self):
        """
        [AC, AD, AH, AS, 2C, 2D, ... KH, KS]
        0 .  1 . 2 . 3 . 4 . 5 .     50, 51
        """
        rank = self.__rank
        if self.__rank == 14:  # for the aces
            rank = 1
        rank -= 1
        return rank * 4 + CARD_SUITS_DICT[self.__suit]

    def __str__(self):  # Following the Treys format of printing
        return INVERSE_RANK_KEY[self.rank] + self.suit[0].lower()

class Strategy:
    def __init__(self):
        self.history = []
        self.hand = []
        self.community_cards = []
        self.CFRplayer = CFRAIPlayer(400)
        self.current_bet = 0
        self.last_opp_amount = 400
        self.last_street = 0

    def new_round(self, round_state, active):
        self.history=[]

        my_cards = round_state.hands[active]
        big_blind = bool(active) # True if you are the big blind

        card1 = my_cards[0][0] + my_cards[0][1] 
        card2 = my_cards[1][0] + my_cards[1][1]
        card = card1+card2
        self.hand.append(card1)
        self.hand.append(card2)

        #May change the order of ...
        if big_blind == 0:
            self.history += ["????"]
            self.history += [card]
            

        if big_blind == 1:
            self.history += [card]
            self.history += ["????"]
        
    
    def play_preflop(self, round_state, active):
        big_blind = bool(active)
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining

        opp_history = self.update_preflop_history(round_state, active)
        if opp_history != None:
            self.history += [opp_history]

        action = self.CFRAIPlayer.get_action(self.history, self.community_cards, my_pip+opp_pip, 800-my_stack-opp_stack, my_stack, 2)
        self.history += [action]

        if action == "k":
            return CheckAction()
        elif action == "c":
            return CallAction()
        elif action == "f":
            return FoldAction()
        else:
            bet = int(action[1:])
            return RaiseAction(bet)
    
    def play_postflop(self, round_state, active):
        big_blind = bool(active)
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take


        if street == 3:
            self.update_preflop_end_history()
            self.history += ["/"]
            for i in range(street):
                self.community_cards.append(board_cards[i])
            self.history += ["".join([str(card) for card in self.community_cards])]
        
        elif street == 4:
            self.update_postflop_end_history()
            self.history += ["/"]
            self.community_cards.append(board_cards[3])
            self.history += ["".join([board_cards[3]])]
        
        elif street == 5:
            self.update_postflop_end_history()
            self.history += ["/"]
            self.community_cards.append(board_cards[5])
            self.history += ["".join([board_cards[5]])]
        
        opp_history = self.update_postflop_history(round_state, active)
        if opp_history != None:
            self.history += [opp_history]
            
        action = self.CFRAIPlayer.get_action(self.history, self.community_cards, my_pip+opp_pip, 800-my_stack-opp_stack, my_stack, 2)
        self.history += [action]

        if action == "k":
            return CheckAction()
        elif action == "c":
            return CallAction()
        elif action == "f":
            return FoldAction()
        else:
            bet = int(action[1:])
            return RaiseAction(bet)

    def update_postflop_history(self, round_state, active):
        big_blind = bool(active)
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively

        oppo_action = ""
        if big_blind:
            if CallAction in legal_actions:
                oppo_action = 'b' + str(self.last_opp_amount-opp_stack)
                self.last_opp_amount = opp_stack
            elif CheckAction in legal_actions:
                oppo_action = "k"
            elif my_stack == opp_stack:
                oppo_action = "c"
            else:
                oppo_action = "f"

        if big_blind == 0:
            if CallAction in legal_actions:
                oppo_action = 'b' + str(self.last_opp_amount-opp_stack)
                self.last_opp_amount = opp_stack
            if CheckAction in legal_actions:
                oppo_action = None
        
        return oppo_action
    
    def update_preflop_history(self, round_state, active):
        big_blind = bool(active)
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        oppo_action = ""
        if big_blind:
            if CheckAction in legal_actions:
                oppo_action = "c"
            if CallAction in legal_actions:
                oppo_action = 'b' + str(self.last_opp_amount-opp_stack)
                self.last_opp_amount = opp_stack
        
        if big_blind == 0:
            if CallAction in legal_actions:
                if opp_stack == 398:
                    oppo_action = None
                else:
                    oppo_action = 'b' + str(self.last_opp_amount-opp_stack)
                    self.last_opp_amount = opp_stack
        
        return oppo_action
            


    
    def update_postflop_end_history(self):
        if self.history[-1] == 'k' and self.history[-2] != 'k':
            self.history += ['k']
        elif self.hsitory[-1][0] == "b":
            self.history += ['c']
    
    def update_preflop_end_history(self):
        if self.history[-1] == 'c':
            self.history += ['k']
        elif self.hsitory[-1][0] == "b":
            self.history += ['c']
            

                    
        

            

        

        


        


