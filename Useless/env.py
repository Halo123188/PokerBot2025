env.add_player()
env.add_AI_player() # Oponent
env.start_new_round()

env.handle_game_stage()


-> env.play_current_stage -> place_bet() -> move_to_next_game_stage()



play_preflop():
1. Bet
2. add cards to hand
3. add cards to history

play_current_stage():
1. both bets
2. action adds to history

place_bets() -> get_action()


重点是 place_bet()