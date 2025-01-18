from typing import List
import fast_evaluator
from phevaluator import evaluate_cards
import random
import matplotlib.pyplot as plt
import time
import numpy as np
import os
from utils import get_filenames
import joblib
from joblib import Parallel, delayed
from tqdm import tqdm
from fast_evaluator import phEvaluatorSetup
import argparse
from sklearn.cluster import KMeans

USE_KMEANS = True  # use kmeans if you want to cluster by equity distribution (more refined, but less accurate)
NUM_FLOP_CLUSTERS = 10
NUM_TURN_CLUSTERS = 10
NUM_RIVER_CLUSTERS = 10

NUM_BINS = 10

def load_kmeans_classifiers():
    global kmeans_flop, kmeans_turn

    filename = sorted(get_filenames(f"../kmeans_data/kmeans/flop"))[-1]
    print("Loading KMeans Flop Classifier", filename)
    kmeans_flop = joblib.load(f"../kmeans_data/kmeans/flop/{filename}")

    filename = sorted(get_filenames(f"../kmeans_data/kmeans/turn"))[-1]
    print("Loading KMeans Turn Classifier", filename)
    kmeans_turn = joblib.load(f"../kmeans_data/kmeans/turn/{filename}")

    assert len(kmeans_flop.cluster_centers_) == NUM_FLOP_CLUSTERS
    assert len(kmeans_turn.cluster_centers_) == NUM_TURN_CLUSTERS

    return kmeans_flop, kmeans_turn

def get_preflop_cluster_id(two_cards_string):  # Lossless abstraction for pre-flop, 169 clusters
    # cards input ex: Ak2h or ['Ak', '2h']
    """
    For the Pre-flop, we can make a lossless abstraction with exactly 169 buckets. The idea here is that what specific suits
    our private cards are doesn't matter. The only thing that matters is whether both cards are suited or not.

    This is how the number 169 is calculated:
    - For cards that are not pocket pairs, we have (13 choose 2) = 13 * 12 / 2 = 78 buckets (since order doesn't matter)
    - These cards that are not pocket pairs can also be suited, so we must differentiate them. We have 78 * 2 = 156 buckets
    - Finally, for cards that are pocket pairs, we have 13 extra buckets (Pair of Aces, Pair of 2, ... Pair Kings). 156 + 13 = 169 buckets

    Note that a pair cannot be suited, so we don't need to multiply by 2.

    Cluster ids:
    1-13 -> pockets
    14-91 -> Unsuited cluster pairs that are not pockets
    92-169 -> Suited cluster pairs that are not pockets

    """
    if type(two_cards_string) == list:
        two_cards_string = "".join(two_cards_string)

    assert len(two_cards_string) == 4

    KEY = {
        "A": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,  # Supports both "T" and "10" as 10
        "7": 7,
        "8": 8,
        "9": 9,
        "T": 10,
        "10": 10,
        "J": 11,
        "Q": 12,
        "K": 13,
    }

    cluster_id = 0

    def hash_(a, b):
        """
        A2/2A -> 1
        A3/3A -> 2
        A4/4A -> 3
        ...
        KQ/QK -> 78

        returns values ranging from 1 to 78
        """
        assert a != b
        assert len(a) == 1 and len(b) == 1
        first = min(KEY[a], KEY[b])
        second = max(KEY[a], KEY[b])

        def sum(b):
            if b <= 1:
                return 0
            n = b - 1
            a = 12
            l = 12 - (b - 2)
            return (n * (a + l)) // 2

        ans = sum(first) + (second - first)
        return int(ans)

    if two_cards_string[0] == two_cards_string[2]:  # pockets
        cluster_id = KEY[two_cards_string[0]]
    elif two_cards_string[1] != two_cards_string[3]:  # unsuited that are not pockets
        cluster_id = 13 + hash_(two_cards_string[0], two_cards_string[2])
    else:  # suited that are not pockets
        cluster_id = 91 + hash_(two_cards_string[0], two_cards_string[2])

    assert cluster_id >= 1 and cluster_id <= 169

    return cluster_id

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


def calculate_equity(player_cards: List[str], community_cards=[], n=2000, timer=False):
    if timer:
        start_time = time.time()
    wins = 0
    deck = fast_evaluator.Deck(excluded_cards=player_cards + community_cards)

    for _ in range(n):
        random.shuffle(deck)
        opponent_cards = deck[:2]  # To avoid creating redundant copies
        player_score = evaluate_cards(
            *(player_cards + community_cards + deck[2 : 2 + (5 - len(community_cards))])
        )
        opponent_score = evaluate_cards(
            *(opponent_cards + community_cards + deck[2 : 2 + (5 - len(community_cards))])
        )
        if player_score < opponent_score:
            wins += 1
        elif player_score == opponent_score:
            wins += 1
            # wins += 0.5

    if timer:
        print("Time it takes to call function: {}s".format(time.time() - start_time))

    return wins / n

def predict_cluster_fast(cards, n=2000, total_clusters=10):
    assert type(cards) == list
    equity = calculate_equity(cards[:2], cards[2:], n=n)
    cluster = min(total_clusters - 1, int(equity * total_clusters))
    return cluster
