import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam


class DQN(nn.Module):
    def __init__(self, init_space, action_space):
        super(DQN, self).__init__()
        self.layer1 = nn.Linear(init_space, 32)
        # self.layer2 = nn.Linear(32, 64)
        self.layer2 = nn.Linear(32, action_space)
        self.relu = nn.ReLU()
        # self.softmax = nn.Softmax()

    def forward(self, x):
        mid1 = self.relu(self.layer1(x))
        # mid2 = self.relu(self.layer2(mid1))
        return self.layer2(mid1)


loss = nn.MSELoss()
optimizer = Adam
