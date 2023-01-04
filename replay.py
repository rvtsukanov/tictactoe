import torch
from rl import TicTacToe

MODEL_NAME = "dc8f1.model"

model = torch.load(f"./models/{MODEL_NAME}")
model.eval()

WHOAMI = "X"

game = TicTacToe((3, 3), "random")
state = game.reset()

# game.deck.render_console()
# act = model(torch.Tensor(game.ohe_deck))


for steps in range(int(1e6)):
    action = model(torch.Tensor(state)).argmax()
    print(model(torch.Tensor(state)))
    print(f"Choosen act: {action} | \n {model(torch.Tensor(state))}")
    next_state, reward, done = game.step(action=action)
    # print(f'Rew: {reward}')
    game.deck.render_console()

    state = next_state

    if done:
        print(f"Reward: {reward}")
        break
