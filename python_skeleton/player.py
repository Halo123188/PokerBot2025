'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import random
import joblib
import numpy as np
from deuces import Deck, Card, Evaluator
import time

class Player(Bot):
    '''
    A pokerbot.
    '''

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        #self.model = joblib.load("pokerbot_model.joblib")

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_cards = round_state.hands[active]  # your cards
        big_blind = bool(active)  # True if you are the big blind
        my_bounty = round_state.bounties[active]  # your current bounty rank
        #pass

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed

        my_bounty_hit = terminal_state.bounty_hits[active]  # True if you hit bounty
        opponent_bounty_hit = terminal_state.bounty_hits[1-active] # True if opponent hit bounty
        bounty_rank = previous_state.bounties[active]  # your bounty rank

        # The following is a demonstration of accessing illegal information (will not work)
        opponent_bounty_rank = previous_state.bounties[1-active]  # attempting to grab opponent's bounty rank

        if my_bounty_hit:
            print("I hit my bounty of " + bounty_rank + "!")
        if opponent_bounty_hit:
            print("Opponent hit their bounty of " + opponent_bounty_rank + "!")

    def infer_opponent_action(previous_state, current_state, active):
        """
        Infers the opponent's last action based on state changes.

        Arguments:
        - previous_state: The previous RoundState before this action.
        - current_state: The current RoundState after the action.
        - active: The index of your player (0 or 1).

        Returns:
        - A string describing the opponent's action.
        """
        if previous_state is None:
            return "No previous state, round just started."

        opponent = 1 - active  # Opponent's index
        prev_pip = previous_state.pips[opponent]
        curr_pip = current_state.pips[opponent]
        prev_stack = previous_state.stacks[opponent]
        curr_stack = current_state.stacks[opponent]

        continue_cost = current_state.pips[opponent] - previous_state.pips[active]

        # Opponent Folded
        if isinstance(current_state, TerminalState):
            print("Opponent Folded")

        # Opponent Raised
        elif curr_pip > prev_pip and curr_stack < prev_stack:
            print(f"Opponent Raised to {curr_pip}")

        # Opponent Called
        elif continue_cost > 0 and curr_pip == prev_pip and curr_stack < prev_stack:
            print("Opponent Called")

        # Opponent Checked
        elif curr_pip == prev_pip and continue_cost == 0:
            print("Opponent Checked")
        else:
            print("Opponent action unclear")

    def get_action(self, game_state, round_state, terminal_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_bounty = round_state.bounties[active]  # your current bounty rank
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot

        '''my_bankroll = game_state.bankroll
        if my_bankroll >= 3500 and FoldAction in legal_actions:
            return FoldAction()

        # Feature extraction for model
        features = np.array([
            len(my_cards),        # Number of cards in hand (should be 2)
            street,               # Current street (0 = preflop, 3 = river)
            my_pip,               # Chips contributed this round
            opp_pip,              # Opponent's chips contributed this round
            my_stack,             # My remaining stack
            opp_stack,            # Opponent's remaining stack
            continue_cost,        # Cost to continue
            my_contribution,      # My total contribution to the pot
            opp_contribution,     # Opponent's total contribution to the pot
        ]).reshape(1, -1)  # Reshape for model input

        # Predict action
        action_probabilities = self.model.predict_proba(features)[0]
        actions = ['fold', 'call', 'raise']
        best_action = actions[np.argmax(action_probabilities)]

        # Convert model action to skeleton action
        if best_action == 'fold' and FoldAction in legal_actions:
            return FoldAction()
        elif best_action == 'call' and CallAction in legal_actions:
            return CallAction()
        elif best_action == 'raise' and RaiseAction in legal_actions:
            raise_amount = min(my_stack, opp_stack)  # Example: go all-in
            return RaiseAction(raise_amount)
        elif CheckAction in legal_actions:
            return CheckAction()  # Default to check if possible
        else:
            return CallAction()  # Default to call if nothing else is possible'''
        previous_state = terminal_state.previous_state
        self.infer_opponent_action(previous_state, game_state, active)
        if RaiseAction in legal_actions:
           min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
           min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
           max_cost = max_raise - my_pip  # the cost of a maximum bet/raise
        if RaiseAction in legal_actions:
            if random.random() < 0.5:
                return RaiseAction(min_raise)
        if CheckAction in legal_actions:  # check-call
            return CheckAction()
        if random.random() < 0.25:
            return FoldAction()
        return CallAction()

if __name__ == '__main__':
    run_bot(Player(), parse_args())
