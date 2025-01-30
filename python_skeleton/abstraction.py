from deuces import Deck, Card, Evaluator
import time

#modify to whatever amt u want
NUM_FLOP_CLUSTERS = 10
NUM_TURN_CLUSTERS = 10
NUM_RIVER_CLUSTERS = 10
DECK = Deck.GetFullDeck()
for card in DECK:
    DECK[DECK.index(card)] = Card.int_to_str(card)


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
