from poker.action import Action
from poker.game_state import GameState
from poker.card import *

def myAI(state: GameState) -> Action:
    return defaultAI(state)

def defaultAI(state: GameState) -> Action:
    to_call = max(player.chips_bet for player in state.players) - state.my_player.chips_bet
    preFlopHandRange = generatePreFlopCards()

    hole_cards = tuple(state.my_player.hole_cards)
    reverse_hole_cards = (hole_cards[1], hole_cards[0]) 

    is_premium_hand = hole_cards in preFlopHandRange or reverse_hole_cards in preFlopHandRange

    if is_premium_hand and len(state.community_cards) == 0:
        return Action.raise_by(state.my_player.chips_in_stack) if to_call > 0 else Action.check()

    return Action.check() if to_call == 0 else Action.fold()

def generatePreFlopCards():
    # Helper dictionary to map chart symbols to the Rank enum
    rank_map = {
            'A': Rank.ACE, 'K': Rank.KING, 'Q': Rank.QUEEN, 'J': Rank.JACK,
            'T': Rank.TEN, '9': Rank.NINE, '8': Rank.EIGHT, '7': Rank.SEVEN,
            '6': Rank.SIX, '5': Rank.FIVE, '4': Rank.FOUR, '3': Rank.THREE, '2': Rank.TWO
            }

    # The specific hands highlighted in red from the image
    red_hands_pairs = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66']
    red_hands_suited = ['AK', 'AQ', 'AJ', 'AT', 'A9', 'A8', 'A7', 'A6', 'A5', 'A4', 'A3', 'A2',
                        'KQ', 'KJ', 'KT', 'QJ', 'QT', 'JT', 'T9', '98']
    red_hands_offsuit = ['AK', 'AQ', 'AJ', 'AT', 'KQ', 'KJ']

    pre_flop_cards = []

    # 1. Generate Pocket Pairs (6 combinations per pair)
    for pair in red_hands_pairs:
        rank = rank_map[pair[0]]
        suits = list(Suit)
        for i in range(len(suits)):
            for j in range(i + 1, len(suits)):
                pre_flop_cards.append((Card(rank, suits[i]), Card(rank, suits[j])))

    # 2. Generate Suited Hands (4 combinations per hand)
    for hand in red_hands_suited:
        rank1, rank2 = rank_map[hand[0]], rank_map[hand[1]]
        for suit in Suit:
            pre_flop_cards.append((Card(rank1, suit), Card(rank2, suit)))

    # 3. Generate Offsuit Hands (12 combinations per hand)
    for hand in red_hands_offsuit:
        rank1, rank2 = rank_map[hand[0]], rank_map[hand[1]]
        suits = list(Suit)
        for suit1 in suits:
            for suit2 in suits:
                if suit1 != suit2:
                    pre_flop_cards.append((Card(rank1, suit1), Card(rank2, suit2)))

    return pre_flop_cards

