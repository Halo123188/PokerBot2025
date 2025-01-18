from typing import List
import random
import glob
import os
from joblib import Parallel, delayed, load

# Constants
NUM_FLOP_CLUSTERS = 10
NUM_TURN_CLUSTERS = 10
NUM_RIVER_CLUSTERS = 10
NUM_BINS = 10

# Utility Functions
def get_all_filenames(path, extension=""):
    """Retrieve filenames with a specific extension from a directory."""
    return [
        os.path.basename(file_path)
        for file_path in glob.glob(os.path.join(path, "*" + extension))
    ]

def initialize_kmeans():
    """Load KMeans classifiers for flop and turn clustering."""
    flop_files = get_all_filenames("../kmeans_data/kmeans/flop")
    turn_files = get_all_filenames("../kmeans_data/kmeans/turn")

    flop_classifier = load(f"../kmeans_data/kmeans/flop/{sorted(flop_files)[-1]}")
    turn_classifier = load(f"../kmeans_data/kmeans/turn/{sorted(turn_files)[-1]}")

    if len(flop_classifier.cluster_centers_) != NUM_FLOP_CLUSTERS:
        raise ValueError("Unexpected number of flop clusters.")
    if len(turn_classifier.cluster_centers_) != NUM_TURN_CLUSTERS:
        raise ValueError("Unexpected number of turn clusters.")

    return flop_classifier, turn_classifier

# Card Clustering and Abstraction
def classify_preflop_hand(cards):
    """Classify preflop hands into 169 clusters."""
    # Ensure cards are in string format
    if isinstance(cards, list):
        cards = "".join(cards)

    RANKS = {"A": 1, "K": 13, "Q": 12, "J": 11, "T": 10, **{str(i): i for i in range(2, 10)}}

    def pair_hash(rank1, rank2):
        """Compute a unique hash for unsuited card pairs."""
        low, high = sorted((RANKS[rank1], RANKS[rank2]))
        return (low - 1) * (13 - low // 2) + high - low

    rank1, suit1 = cards[0], cards[1]
    rank2, suit2 = cards[2], cards[3]

    if rank1 == rank2:
        return RANKS[rank1]
    if suit1 == suit2:
        return 91 + pair_hash(rank1, rank2)
    return 13 + pair_hash(rank1, rank2)

# Deck Generation
def create_shuffled_deck(excluded=[]):
    """Generate a shuffled deck, excluding specific cards."""
    suits = "hdsc"
    ranks = "A23456789TJQK"
    deck = [rank + suit for rank in ranks for suit in suits if rank + suit not in excluded]
    random.shuffle(deck)
    return deck

# Equity Calculation
def compute_equity(player_cards, community_cards=[], iterations=2000):
    """Simulate the equity of a hand using Monte Carlo."""
    wins = 0
    deck = create_shuffled_deck(player_cards + community_cards)

    for _ in range(iterations):
        random.shuffle(deck)
        opponent_hand = deck[:2]
        remaining_board = deck[2:2 + (5 - len(community_cards))]
        player_score = evaluate_cards(*(player_cards + community_cards + remaining_board))
        opponent_score = evaluate_cards(*(opponent_hand + community_cards + remaining_board))
        wins += (player_score <= opponent_score)

    return wins / iterations

def equity_distribution(player_cards, community_cards=[], bins=10, samples=200, parallel=False):
    """Generate an equity histogram for a hand."""
    deck = create_shuffled_deck(player_cards + community_cards)
    histogram = [0] * bins

    def simulate():
        random.shuffle(deck)
        sample_cards = deck[:1 if len(community_cards) < 5 else 0]
        equity = compute_equity(player_cards, community_cards + sample_cards, iterations=100)
        return min(int(equity * bins), bins - 1)

    results = Parallel(n_jobs=-1)(delayed(simulate)() for _ in range(samples)) if parallel else [simulate() for _ in range(samples)]
    for result in results:
        histogram[result] += 1

    return [value / samples for value in histogram]

# Fast Cluster Prediction
def fast_cluster_prediction(cards, clusters=10, iterations=2000):
    """Quickly predict a cluster for a given hand."""
    equity = compute_equity(cards[:2], cards[2:], iterations)
    return min(clusters - 1, int(equity * clusters))
