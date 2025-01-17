from typing import NewType, List
from abstraction import predict_cluster
import abstraction

DISCRETE_ACTIONS = ["k", "bMIN", "bMAX", "c", "f"]

Action = NewType("Action", str)

class PostflopHoldemHistory():
    """
    Example of history:
    First two actions are the cards dealt to the players. The rest of the actions are the actions taken by the players.
            1. ['AkTh', 'QdKd', '/', 'QhJdKs', 'bMIN', 'c', '/', 'Ah', 'k', 'k', ...]

    Notice that there are no bets on the preflop, as this is the postflop version of the game.

    Infoset:
    [4, 'bMIN', 'c', '10', 'k', 'k', ...]


    Every round starts the same way:
    Small blind = 1 chip
    Big blind = 2 chips

    Total chips = 100BB per player.
    Minimum raise = X to match bet, and Y is the raise amount
    If no raise before, then the minimum raise amount is 2x the bet amount (preflop would be 2x big blind).
    Else it is whatever was previously raised. This is not the same as 2x the previous bet amount. Just the Y raise amount.

    Ex: The bet is 10$. I raise to 50$, so I raised by 40$ (Y = 40). The next player's minimum raise is not 100$, but rather to 90$, since (it's 50$ to match the bet, and 40$ to match the raise).

    Minimum bet = 1 chip (0.5BB)

    The API for the history is inspired from the Slumbot API, https://www.slumbot.com/

    I want to avoid all the extra overhead, so taking inspiration from `environment.py` with the `PokerEnvironment`
    """

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

def predict_cluster_kmeans(kmeans_classifier, cards, n=200):
    """cards is a list of cards"""
    assert type(cards) == list
    equity_distribution = calculate_equity_distribution(cards[:2], cards[2:], n=n)
    y = kmeans_classifier.predict([equity_distribution])
    assert len(y) == 1
    return y[0]

def predict_cluster(cards):
    assert type(cards) == list

    if USE_KMEANS:
        if len(cards) == 5:  # flop
            return predict_cluster_kmeans(kmeans_flop, cards)
        elif len(cards) == 6:  # turn
            return predict_cluster_kmeans(kmeans_turn, cards)
        elif len(cards) == 7:  # river
            return predict_cluster_fast(cards, total_clusters=NUM_RIVER_CLUSTERS)
        else:
            raise ValueError("Invalid number of cards: ", len(cards))
    else:
        if len(cards) == 5:  # flop
            return predict_cluster_fast(cards, total_clusters=NUM_FLOP_CLUSTERS)
        elif len(cards) == 6:  # turn
            return predict_cluster_fast(cards, total_clusters=NUM_TURN_CLUSTERS)
        elif len(cards) == 7:  # river
            return predict_cluster_fast(cards, total_clusters=NUM_RIVER_CLUSTERS)
        else:
            raise ValueError("Invalid number of cards: ", len(cards))

def calculate_equity_distribution(
    player_cards: List[str], community_cards=[], bins=NUM_BINS, n=200, timer=False, parallel=False
):
    """
    Return
            equity_hist - Histogram as a list of "bins" elements

    n = # of cards to sample from the next round to generate this distribution.

    There is a tradeoff between the execution speed and variance of the values calculated, since
    we are using a monte-carlo method to calculate those equites. In the end, I found a bin=5, n=100
    and rollouts using 100 values to be a good approximation. We won't be using this method for
    pre-flop, since we can have a lossless abstraction of that method anyways.

    The equity distribution is a better way to represent the strength of a given hand. It represents
    how well a given hand performs over various profiles of community cards. We can calculate
    the equity distribution of a hand at the following game stages: flop (we are given no community cards), turn (given 3 community cards) and river (given 4 community cards).

    if we want to generate a distribution for the EHS of the turn (so we are given our private cards + 3 community cards),
    we draw various turn cards, and calculate the equity using those turn cards.
    If we find for a given turn card that its equity is 0.645, and we have 10 bins, we would increment the bin 0.60-0.70 by one.
    We repeat this process until we get enough turn card samples.
    """
    if timer:
        start_time = time.time()
    equity_hist = [
        0 for _ in range(bins)
    ]  # histogram of equities, where equity[i] represents the probability of the i-th bin

    assert len(community_cards) != 1 and len(community_cards) != 2

    deck = fast_evaluator.Deck(excluded_cards=player_cards + community_cards)

    def sample_equity():
        random.shuffle(deck)
        if len(community_cards) == 0:
            score = calculate_equity(player_cards, community_cards + deck[:3], n=200)
        elif len(community_cards) < 5:
            score = calculate_equity(player_cards, community_cards + deck[:1], n=100)
        else:
            score = calculate_equity(player_cards, community_cards, n=100)

        # equity_hist[min(int(score * bins), bins-1)] += 1.0 # Score of the closest bucket is incremented by 1
        return min(int(score * bins), bins - 1)

    if parallel:  # Computing these equity distributions in parallel is much faster
        equity_bin_list = Parallel(n_jobs=-1)(delayed(sample_equity)() for _ in range(n))

    else:
        equity_bin_list = [sample_equity() for _ in range(n)]

    for bin_i in equity_bin_list:
        equity_hist[bin_i] += 1.0

    # Normalize the equity so that the probability mass function (p.m.f.) of the distribution sums to 1
    for i in range(bins):
        equity_hist[i] /= n

    if timer:
        print("Time to calculate equity distribution: ", time.time() - start_time)
    return equity_hist
