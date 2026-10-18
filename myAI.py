from poker.action import Action
from poker.game_state import GameState
from poker.card import *

def myAI(state: GameState) -> Action:
    return defaultAI(state)

rank_values = {
    Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
    Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
    Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13, Rank.ACE: 14
}

def generatePreFlopCards():
    rank_map = {
            'A': Rank.ACE, 'K': Rank.KING, 'Q': Rank.QUEEN, 'J': Rank.JACK,
            'T': Rank.TEN, '9': Rank.NINE, '8': Rank.EIGHT, '7': Rank.SEVEN,
            '6': Rank.SIX, '5': Rank.FIVE, '4': Rank.FOUR, '3': Rank.THREE, '2': Rank.TWO
            }

    hands_pairs = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66']
    hands_suited = ['AK', 'AQ', 'AJ', 'AT', 'A9', 'A8', 'A7', 'A6', 'A5', 'A4', 'A3', 'A2',
                        'KQ', 'KJ', 'KT', 'QJ', 'QT', 'JT', 'T9', '98']
    hands_offsuit = ['AK', 'AQ', 'AJ', 'AT', 'KQ', 'KJ']

    pre_flop_cards = []

    for pair in hands_pairs:
        rank = rank_map[pair[0]]
        suits = list(Suit)
        for i in range(len(suits)):
            for j in range(i + 1, len(suits)):
                pre_flop_cards.append((Card(rank, suits[i]), Card(rank, suits[j])))

    for hand in hands_suited:
        rank1, rank2 = rank_map[hand[0]], rank_map[hand[1]]
        for suit in Suit:
            pre_flop_cards.append((Card(rank1, suit), Card(rank2, suit)))

    for hand in hands_offsuit:
        rank1, rank2 = rank_map[hand[0]], rank_map[hand[1]]
        suits = list(Suit)
        for suit1 in suits:
            for suit2 in suits:
                if suit1 != suit2:
                    pre_flop_cards.append((Card(rank1, suit1), Card(rank2, suit2)))

    return pre_flop_cards

PRE_FLOP_HAND_RANGE = generatePreFlopCards()

def defaultAI(state: GameState) -> Action:
    to_call = max(player.chips_bet for player in state.players) - state.my_player.chips_bet

    hole_cards = tuple(state.my_player.hole_cards)
    reverse_hole_cards = (hole_cards[1], hole_cards[0]) 

    is_premium_hand = hole_cards in PRE_FLOP_HAND_RANGE or reverse_hole_cards in PRE_FLOP_HAND_RANGE
    is_pair = hole_cards[0].rank == hole_cards[1].rank

    is_suited = hole_cards[0].suit == hole_cards[1].suit
    val1 = rank_values[hole_cards[0].rank]
    val2 = rank_values[hole_cards[1].rank]
    is_suited_connector = is_suited and abs(val1 - val2) == 1 and min(val1, val2) >= 4


    # edwards BS
    is_offSuit = not is_suited
    is_edward = hole_cards[0].rank == Rank.SEVEN and hole_cards[1].rank == Rank.TWO and is_offSuit

    match len(state.community_cards):
        case 0:
            return playPreFlop(state, is_edward, is_premium_hand, is_pair, is_suited_connector, to_call)
        case 3 | 4:
            # made hand check
            current_strength = calculate_hand_strength(hole_cards, state.community_cards)

            if current_strength >= 0.40:
                if current_strength >= 0.60 and to_call == 0:
                    return Action.raise_by(state.big_blind * 3)
                return Action.call() if to_call > 0 else Action.check()

            # profitable draw check
            risk = to_call
            reward = risk + state.chips_in_pot
            pot_odds = risk / reward if reward > 0 else 0.0

            outs = count_outs(hole_cards, state.community_cards)
            cards_to_come = 5 - len(state.community_cards)
            multiplier = 4 if cards_to_come == 2 else 2
            equity = (outs * multiplier) / 100.0

            if equity > pot_odds:
                if equity > 0.5 and to_call == 0:
                    return Action.raise_by(state.big_blind * 2)
                return Action.call() if to_call > 0 else Action.check()

            return Action.check() if to_call == 0 else Action.fold()

        case 5:
            hand_strength = calculate_hand_strength(hole_cards, state.community_cards)
            return playRiver(state, to_call, hand_strength)

    return Action.check() if to_call == 0 else Action.fold()

def count_outs(hole_cards, community_cards):
    all_cards = list(hole_cards) + list(community_cards)
    outs = 0

    # flush
    suits = [card.suit for card in all_cards]
    flush_suit = None
    for suit in Suit:
        if suits.count(suit) >= 4:
            outs += 9
            flush_suit = suit
            break

    # straights
    present_values = set(rank_values[card.rank] for card in all_cards)
    if 14 in present_values:
        present_values.add(1)

    straight_outs = set()
    for low_end in range(1, 11):
        window = set(range(low_end, low_end + 5))
        intersection = window.intersection(present_values)
        if len(intersection) == 4:
            missing_rank = (window - intersection).pop()
            straight_outs.add(missing_rank)

    for rank_val in straight_outs:
        if flush_suit:
            outs += 3
        else:
            outs += 4

    # pairs, three of a kind, full house
    ranks = [card.rank for card in all_cards]
    counts = [ranks.count(rank) for rank in set(ranks)]
    
    pairs = counts.count(2)
    threes = counts.count(3)

    if threes > 0:
        outs += 1 
        board_ranks = set([card.rank for card in community_cards])
        for br in board_ranks:
            if ranks.count(br) == 1:
                outs += 3
    elif pairs >= 2:
        outs += 4
    elif pairs == 1:
        outs += 2
    else:
        pass

    unseen_cards = 52 - len(all_cards)
    return min(outs, unseen_cards)

def playPreFlop(state: GameState, is_edward: bool, is_premium_hand: bool, is_pair: bool, is_suited_connector: bool, to_call: int):
    if is_edward:
        return Action.raise_by(state.my_player.chips_in_stack)

    if is_premium_hand:
        raise_amount = 0
        if is_pair:
            raise_amount = max(state.big_blind * 4, to_call * 2)
        else:
            raise_amount = max(state.big_blind * 2, to_call * 2)

        return Action.raise_by(raise_amount)

    if is_pair or is_suited_connector:
        if to_call <= state.big_blind * 3:
            return Action.call() if to_call > 0 else Action.check()
        else:
            return Action.fold()

    return Action.check() if to_call == 0 else Action.fold()

def playRiver(state: GameState, to_call: int, hand_strength: float):
    if hand_strength >= 0.9:
        if to_call == 0:
            return Action.raise_by(state.chips_in_pot // 2)
        else:
            return Action.raise_by(state.chips_in_pot)
    elif hand_strength >= 0.3:
        if to_call == 0:
            return Action.check()
        else:
            risk = to_call
            reward = risk + state.chips_in_pot
            pot_odds = risk / reward

            return Action.call() if hand_strength > pot_odds else Action.fold()
    else:
        return Action.check() if to_call == 0 else Action.fold()

def calculate_hand_strength(hole_cards, community_cards):
    all_cards = list(hole_cards) + list(community_cards)
    
    # flush
    suits = [card.suit for card in all_cards]
    is_flush = any(suits.count(suit) >= 5 for suit in Suit)

    # straight
    present_values = set(rank_values[card.rank] for card in all_cards)
    # low ace
    if 14 in present_values:
        present_values.add(1)

    is_straight = False
    for low_end in range(1, 11):
        if set(range(low_end, low_end + 5)).issubset(present_values):
            is_straight = True
            break

    # pair three, four
    ranks = [card.rank for card in all_cards]
    counts = [ranks.count(rank) for rank in set(ranks)]

    pairs = counts.count(2)
    threes = counts.count(3)
    quads = counts.count(4)

    is_full_house = (threes > 0 and pairs > 0) or threes > 1

    # hole cards used for pair, three, four check
    hole_ranks = [card.rank for card in hole_cards]
    board_ranks = [card.rank for card in community_cards]

    hole_contributed = (hole_ranks[0] == hole_ranks[1]) or (hole_ranks[0] in board_ranks) or (hole_ranks[1] in board_ranks)

    board_suits = [card.suit for card in community_cards]
    flush_possible = any(board_suits.count(suit) >= 3 for suit in Suit)

    if is_flush and is_straight:
        return 0.95 # Straight Flush
    elif quads > 0:
        return 0.95 if hole_contributed else 0.10 # Four of a kind
    elif is_full_house:
        return 0.95 if hole_contributed else 0.10 # Full House
    elif is_flush:
        return 0.90 # Flush
    elif is_straight:
        return 0.90 if not flush_possible else 0.85 # Straight
    elif threes > 0:
        return 0.70 if hole_contributed else 0.10 # Three of a Kind
    elif pairs >= 2:
        return 0.60 if hole_contributed else 0.10 # Two Pair
    elif pairs == 1:
        return 0.40 if hole_contributed else 0.10 # One Pair
    else:
        return 0.10 # High Card
