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
from typing import List
import copy
from aiplayer import CFRAIPlayer


class Player(Bot, CFRAIPlayer):
    '''
    A pokerbot.
    '''

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.
        '''
        super().__init__(STARTING_STACK)
        self.preflop_infosets = joblib.load("preflop_infoSets_batch_19.joblib")
        self.postflop_infosets = joblib.load("postflop_infoSets_batch_19.joblib")

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
        
        if my_bounty_hit:
            print("I hit my bounty of " + bounty_rank + "!")
        if opponent_bounty_hit:
            print("Opponent hit their bounty of " + opponent_bounty_rank + "!")

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

        if my_bounty_hit:
            print("I hit my bounty of " + bounty_rank + "!")
        if opponent_bounty_hit:
            print("Opponent hit their bounty of " + opponent_bounty_rank + "!")


    def perform_preflop_abstraction(self, history, BIG_BLIND=2):
        stage = copy.deepcopy(history)
        abstracted_history = stage[:2]
        if (
            len(stage) >= 6 and stage[3] != "c"  # bet seqeuence of length 4
        ):  # length 6 that isn't a call, we need to condense down
            if len(stage) % 2 == 0:
                abstracted_history += ["bMAX"]
            else:
                abstracted_history += ["bMIN", "bMAX"]
        else:
            bet_size = BIG_BLIND
            pot_total = BIG_BLIND + int(BIG_BLIND / 2)
            for i, action in enumerate(stage[2:]):
                if action[0] == "b":
                    bet_size = int(action[1:])

                    # this is a raise on a small bet
                    if abstracted_history[-1] == "bMIN":
                        if bet_size <= 2 * pot_total:
                            abstracted_history += ["bMID"]
                        else:
                            abstracted_history += ["bMAX"]
                    elif abstracted_history[-1] == "bMID":
                        abstracted_history += ["bMAX"]
                    elif abstracted_history[-1] == "bMAX":
                        if abstracted_history[-2] == "bMID":
                            abstracted_history[-2] = "bMIN"
                        abstracted_history[-1] = "bMID"
                        abstracted_history += ["bMAX"]
                    else:  # first bet
                        if bet_size <= pot_total:
                            abstracted_history += ["bMIN"]
                        elif bet_size <= 2 * pot_total:
                            abstracted_history += ["bMID"]
                        else:
                            abstracted_history += ["bMAX"]

                    pot_total += bet_size

                elif action == "c":
                    pot_total = 2 * bet_size
                    abstracted_history += ["c"]
                else:
                    abstracted_history += [action]
        return abstracted_history

    def perform_postflop_abstraction(self, history, BIG_BLIND=2):
        history = copy.deepcopy(history)

        pot_total = BIG_BLIND * 2
        # Compute preflop pot size
        flop_start = history.index("/")
        for i, action in enumerate(history[:flop_start]):
            if action[0] == "b":
                bet_size = int(action[1:])
                pot_total = 2 * bet_size

        # ------- Remove preflop actions + bet abstraction -------
        abstracted_history = history[:2]
        # swap dealer and small blind positions for abstraction
        stage_start = flop_start
        stage = self.get_stage(history[stage_start + 1 :])
        latest_bet = 0
        while True:
            abstracted_history += ["/"]
            if (
                len(stage) >= 4 and stage[3] != "c"
            ):  # length 4 that isn't a call, we need to condense down
                abstracted_history += [stage[0]]

                if stage[-1] == "c":
                    if len(stage) % 2 == 1:  # ended on dealer
                        abstracted_history += ["bMAX", "c"]
                    else:
                        if stage[0] == "k":
                            abstracted_history += ["k", "bMAX", "c"]
                        else:
                            abstracted_history += ["bMIN", "bMAX", "c"]
                else:
                    if len(stage) % 2 == 0:
                        abstracted_history += ["bMAX"]
                    else:
                        abstracted_history += ["bMIN", "bMAX"]
            else:
                for i, action in enumerate(stage):
                    if action[0] == "b":
                        bet_size = int(action[1:])
                        latest_bet = bet_size

                        # this is a raise on a small bet
                        if abstracted_history[-1] == "bMIN":
                            abstracted_history += ["bMAX"]
                        # this is a raise on a big bet
                        elif (
                            abstracted_history[-1] == "bMAX"
                        ):  # opponent raised, first bet must be bMIN
                            abstracted_history[-1] = "bMIN"
                            abstracted_history += ["bMAX"]
                        else:  # first bet
                            if bet_size >= pot_total:
                                abstracted_history += ["bMAX"]
                            else:
                                abstracted_history += ["bMIN"]

                        pot_total += bet_size

                    elif action == "c":
                        pot_total += latest_bet
                        abstracted_history += ["c"]
                    else:
                        abstracted_history += [action]

            # Proceed to next stage or exit if final stage
            if "/" not in history[stage_start + 1 :]:
                break
            stage_start = history[stage_start + 1 :].index("/") + (stage_start + 1)
            stage = self.get_stage(history[stage_start + 1 :])

        return abstracted_history
    
    def get_stage(self, history):
        if "/" in history:
            return history[: history.index("/")]
        else:
            return history
   
    def get_action(self, game_state, round_state, active):
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

        #Version 1 - Logic Bot
        my_cards = round_state.hands[active]
        card1 = my_cards[0]
        card2 = my_cards[1]

        rank1 = card1[0]
        suit1 = card1[1]
        rank2 = card2[0]
        suit2 = card2[1]

        big_blind = bool(active)  # True if you are the big blind

         # Convert cards to string format
        card_str = [str(card) for card in my_cards]
        community_cards = [str(card) for card in board_cards]

        # Reconstruct history (this is a simplified version)
        history = []
        if street > 0:
            history = ['d', 'c', '/']  # Assume dealer called preflop
        if street > 3:
            history.extend(['c', 'c', '/'])  # Assume both checked on flop
        if street > 4:
            history.extend(['c', 'c', '/'])  # Assume both checked on turn

        isDealer = active == 0
        checkAllowed = CheckAction in legal_actions

        action = self.get_cfr_action(
            history,
            card_str,
            community_cards,
            opp_pip,
            my_contribution + opp_pip,
            my_contribution + opp_contribution,
            my_stack,
            BIG_BLIND,
            isDealer,
            checkAllowed
        )

        # Convert CFR action to engine action
        if action.startswith('b'):
            return RaiseAction(int(action[1:]))
        elif action == 'c':
            return CallAction()
        elif action == 'f':
            return FoldAction()
        else:  # action == 'k'
            return CheckAction()
        
    def get_cfr_action(self, history, card_str, community_cards, highest_current_bet, stage_pot_balance, total_pot_balance, player_balance, BIG_BLIND, isDealer, checkAllowed):
        action = None
        SMALLEST_BET = int(BIG_BLIND / 2)

        if len(community_cards) == 0:  # preflop
            abstracted_history = self.perform_preflop_abstraction(history, BIG_BLIND=BIG_BLIND)
            infoset_key = "".join(PreflopHoldemHistory(abstracted_history).get_infoSet_key())
            strategy = self.preflop_infosets[infoset_key].get_average_strategy()
            abstracted_action = get_action(strategy)

            if abstracted_action == "bMIN":
                action = "b" + str(max(BIG_BLIND, int(stage_pot_balance)))
            elif abstracted_action == "bMID":
                action = "b" + str(max(BIG_BLIND, 2 * int(stage_pot_balance)))
            elif abstracted_action == "bMAX":
                action = "b" + str(player_balance)
            else:
                action = abstracted_action
        else:
            abstracted_history = self.perform_postflop_abstraction(history, BIG_BLIND=BIG_BLIND)
            infoset_key = PostflopHoldemHistory(abstracted_history).get_infoSet_key_online()
            strategy = self.postflop_infosets[infoset_key].get_average_strategy()
            abstracted_action = get_action(strategy)

            if abstracted_action == "bMIN":
                action = "b" + str(max(BIG_BLIND, int(1 / 3 * total_pot_balance / SMALLEST_BET) * SMALLEST_BET))
            elif abstracted_action == "bMAX":
                action = "b" + str(min(total_pot_balance, player_balance))
            else:
                action = abstracted_action

        return action

if __name__ == '__main__':
    run_bot(Player(), parse_args())
