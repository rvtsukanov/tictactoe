from rl import TicTacToe, Transition, ReplayMemory
from torch_models import DQN, loss, optimizer
import torch
import random
import math
import numpy as np

from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter()

import matplotlib.pyplot as plt

EPOCHS = int(1e6)
LR = 1e-3
WHOAMI = "X"
DECAY = 4
CAPACITY = 100
BATCH_SIZE = 32
GAMMA = 0.9
LEARN_FREQ = 100  # each 100 steps

POSITIVE_R = 1
NEGATIVE_R = -1
INVARIANT_R = 0.1
BAD_TOUCH_R = -1

EXP_N_SYM = 5


import base64
import hashlib

import time

hash = hashlib.sha1(str(time.time()).encode("UTF-8")).hexdigest()[:EXP_N_SYM]

game = TicTacToe((3, 3), "random")

dqn = DQN(game.observation_dim, game.action_dim)
value_dqn = DQN(game.observation_dim, game.action_dim)

ans = dqn(torch.from_numpy(game.ohe_deck).float())
optimizer = optimizer(params=dqn.parameters(), lr=LR)


def decay_func(x, decay=40):
    return math.exp(-x / decay)


def choose_action_policy(proposed_actions, avaliable_actions_map, n_steps_done):
    # proposed_actions : [0.3, 0.6, 0.1]
    # avail_map: [1, 1, 0]
    # --> [0.33, 0.66, 0]
    # but if e-greedy, then [0.5, 0.5, 0]
    # then random.choice of obtained vector

    mapped_proba = proposed_actions * avaliable_actions_map
    if random.random() > decay_func(n_steps_done, decay=DECAY):
        # too long and non-optimal :c  TODO: re-invent
        probas = [1 / sum(mapped_proba != 0) if i != 0 else 0 for i in mapped_proba]
        # return torch.multinomial(probas, 1)
    else:
        probas = mapped_proba / mapped_proba.sum()

    return torch.multinomial(probas, 1)


def choose_action(proposed_actions, avaliable_actions_map, n_steps_done):
    mapped_proba = proposed_actions * avaliable_actions_map
    mapped_proba_inf = torch.Tensor(
        [-float("inf") if n == 0 else n for n in mapped_proba]
    )
    # if random.random() > decay_func(n_steps_done, decay=DECAY):
    if n_steps_done < 30000:  # :c
        # too long and non-optimal :c  TODO: re-invent
        probas = [1 / sum(mapped_proba != 0) if i != 0 else 0 for i in mapped_proba]
        return torch.multinomial(torch.Tensor(probas), 1)
    else:
        return mapped_proba_inf.argmax()


def choose_action_no_filter(proposed_actions, n_steps_done):
    if n_steps_done < 50000:  # :c
        probas = [1 / len(proposed_actions) for _ in proposed_actions]
        return torch.multinomial(torch.Tensor(probas), 1)
    else:
        return proposed_actions.argmax()


replay_memory = ReplayMemory(CAPACITY)

mean_rew = []
loss_values = []
num_mine_victories = []
num_his_victories = []

for iter in range(EPOCHS):
    state = game.reset()
    transition_store = []

    for steps in range(int(1e6)):

        with torch.no_grad():
            proposed_actions = dqn(torch.from_numpy(state).float())

        # action = choose_action(
        #     proposed_actions, torch.Tensor(game.avaliable_actions_map), iter
        # )

        action = choose_action_no_filter(proposed_actions, iter)

        next_state, reward, done = game.step(action=action)
        transition_store.append(Transition(state, action, next_state, reward))
        state = next_state

        if done:

            writer.add_scalar(
                "Traj. mean reward",
                np.array([t.reward for t in transition_store]).mean(),
                iter,
            )
            writer.add_scalar("Mean traj. len", len(transition_store), iter)

            writer.add_scalar("Our victory", reward == POSITIVE_R, iter)
            writer.add_scalar("His victory", reward == NEGATIVE_R, iter)
            writer.add_scalar("Bad touch", reward == BAD_TOUCH_R, iter)

            reward_row = np.array(
                [
                    t.reward * GAMMA ** (len(transition_store) - n - 1)
                    for n, t in enumerate(transition_store)
                ]
            )
            reward_row = reward_row.cumsum()

            for idx, item in enumerate(transition_store):
                replay_memory.push(
                    Transition(
                        item.state, item.action, item.next_state, reward_row[idx]
                    )
                )
            break

    if len(replay_memory.memory) < BATCH_SIZE:
        pass

    elif iter % LEARN_FREQ == 0:
        # learn model
        transitions = replay_memory.sample(BATCH_SIZE)
        batch = Transition(*zip(*transitions))

        q_values = dqn(torch.Tensor(batch.state))
        right_values = torch.gather(
            q_values,
            1,
            torch.unsqueeze(torch.Tensor(batch.action), 1).type(torch.int64),
        )
        lv = loss(right_values.squeeze(), torch.Tensor(batch.reward))

        writer.add_scalar("Loss/Train", lv, iter)

        optimizer.zero_grad()
        lv.backward()
        optimizer.step()

        print(
            f"[{iter}] [loss:{lv}] Mean traj. reward",
            round(torch.tensor(batch.reward).detach().numpy().mean(), 2),
        )

        mean_rew.append(round(torch.tensor(batch.reward).detach().numpy().mean(), 2))
        loss_values.append(lv.detach())

        torch.save(dqn, f"./models/{hash}.model")

        # plt.plot(np.array(loss_values))
        #
        # if iter % 5000 == 0:
        #     plt.show()


writer.flush()
writer.close()
