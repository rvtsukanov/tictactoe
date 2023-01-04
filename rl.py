from gym import Env
from models import Deck
import numpy as np
import random
from collections import namedtuple, deque

REPLAY_BUFFER = 1000
ETA = 0.9

POSITIVE_R = 1
NEGATIVE_R = -1
INVARIANT_R = 0.1
BAD_TOUCH_R = -1

Transition = namedtuple("Transition", ("state", "action", "next_state", "reward"))


class ReplayMemory(object):
    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, transition):
        """Save a transition"""
        self.memory.append(transition)

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


class TicTacToe:
    """
    RL-env
    X - is me; O - opposite.
    """

    def __init__(self, size, second_player_policy="random"):
        self.size = size
        self.deck = Deck(size=self.size)
        self.second_player_policy = second_player_policy
        self.observation_dim = self.ohe_deck.shape[0]
        self.action_dim = len(self.deck.flatted_deck)

    @property
    def ohe_deck(self):
        return np.squeeze(
            np.eye(len(self.deck.all_signs))[self.deck.encoded_flatted_deck].reshape(-1)
        )

    def step(self, action):
        """
        I am X. It is only a defenition of mine vs not mine steps ahead.
        :param action: index coordinate of making your turn. (For eg for 3x3 env: 2 is (0, 2); 4 -> (1, 1) etc.)
        :return: s_prime, reward, done
        """
        is_mine_victory, is_mine_game_over, is_mine_violated = self.deck.make_step(
            whoami="X", elem_index=action
        )

        if is_mine_violated:
            return self.ohe_deck, BAD_TOUCH_R, is_mine_violated

        is_his_victory, is_his_game_over = False, True

        if self.second_player_policy == "random":
            if not is_mine_game_over:
                is_his_victory, is_his_game_over, _ = self.deck.make_random_step("O")

        reward = INVARIANT_R

        if is_mine_victory:
            reward = POSITIVE_R

        elif is_his_victory:
            reward = NEGATIVE_R

        return self.ohe_deck, reward, is_mine_game_over | is_his_game_over

    @property
    def avaliable_actions_map(self):
        return self.deck.available_actions_map

    def reset(self):
        self.deck = Deck(self.size)
        if random.random() > 0.5:
            self.deck.make_random_step("O")
        return self.ohe_deck
