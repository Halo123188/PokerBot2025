from deuces import Deck, Card, Evaluator
import time
import random

#modify to whatever amt u want
NUM_FLOP_CLUSTERS = 10
NUM_TURN_CLUSTERS = 10
NUM_RIVER_CLUSTERS = 10
DECK = Deck.GetFullDeck()
for card in DECK:
    DECK[DECK.index(card)] = Card.int_to_str(card)

#Jenny's preflop cluster abstraction
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

    return str(bounty_id) + '/' + str(cluster_id)

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
