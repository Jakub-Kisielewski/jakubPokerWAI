from poker.action import Action
from poker.game_state import GameState
from poker.card import Rank

def myAI(state: GameState) -> Action:
    return defaultAI(state)

def defaultAI(state: GameState) -> Action:
    to_call = max(player.chips_bet for player in state.players) - state.my_player.chips_bet

    hole_ranks = tuple(card.rank for card in state.my_player.hole_cards)

    strong_starting_pairs = [
            (Rank.ACE, Rank.ACE),     # AA
            (Rank.ACE, Rank.KING),    # AKs
            (Rank.ACE, Rank.QUEEN),   # AQs
            (Rank.ACE, Rank.JACK),    # AJs
            (Rank.ACE, Rank.TEN),     # ATs

            (Rank.ACE, Rank.KING),    # AKo
            (Rank.KING, Rank.KING),   # KK
            (Rank.KING, Rank.QUEEN),  # KQs

            (Rank.ACE, Rank.QUEEN),   # AQo
            (Rank.QUEEN, Rank.QUEEN), # QQ

            (Rank.ACE, Rank.JACK),    # AJo
            (Rank.JACK, Rank.JACK),   # JJ

            (Rank.TEN, Rank.TEN),     # TT

            (Rank.NINE, Rank.NINE)    # 99
            ]

    if hole_ranks in strong_starting_pairs:
        return Action.raise_by(state.my_player.chips_in_stack)

    return Action.fold()

