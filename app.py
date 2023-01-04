from flask import Flask
from flask import render_template
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, send
import logging
from models import Deck
from flask import Flask, request
import re
from dataclasses import dataclass, field
from typing import List, Optional
import sys
from pydantic import BaseModel
import itertools
from collections import defaultdict
import torch

root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
root.addHandler(handler)
logging.getLogger("werkzeug").setLevel(logging.ERROR)


class GameContext(BaseModel):
    is_mine_turn: Optional[bool]
    whoami_sign: Optional[str]
    deck: Optional[Deck]
    deck_body: Optional[str]
    console_message: Optional[str]
    last_turn_by: Optional[str]

    class Config:
        arbitrary_types_allowed = True


class SocketContext(BaseModel):
    whoami: Optional[str]
    num_players: Optional[int]
    button_id: Optional[str]

    class Config:
        arbitrary_types_allowed = True


class SocketMessage(BaseModel):
    socket_context: Optional[SocketContext]
    game_context: Optional[GameContext]
    extra: Optional[dict]

    class Config:
        arbitrary_types_allowed = True


from rl import TicTacToe

MODEL_NAME = "dc8f1.model"


class Game(Flask):
    template_name = "index.html"

    def __init__(self, name, size=(3, 3), max_players=2):
        super().__init__(name)
        self.size = size
        self.max_players = max_players

        self.players = {}

        self.reset_game()

        self.socket_io = SocketIO(self, logger=False, engineio_logger=False)
        self.register_handlers()
        self.register_socket_handlers()

        self.ai_agent = torch.load(f"./models/{MODEL_NAME}")
        self.ai_agent.eval()

        self.ai_enabled = False

    @property
    def num_players(self):
        return len(self.players)

    @property
    def players_inv(self):
        defaultdict
        return {v: k for k, v in self.players.items()}

    @staticmethod
    def convert_jinja_to_deck(jinja_id):
        return list(map(int, re.findall("(\d)-(\d)", jinja_id)[0]))

    def register_handlers(self):
        self.add_url_rule("/", "/", self.init_handler)

    def register_socket_handlers(self):
        self.socket_io.on_event(
            "connection_established", self.handle_connection_established
        )
        self.socket_io.on_event("button_click", self.handle_button_clicked)
        self.socket_io.on_event("disconnect", self.handle_disconnection)

    def reset_game(self):
        self.deck = Deck(self.size)
        self.turn_generator = itertools.cycle(self.deck.player_signs)
        self.current_turn = None
        self.change_current_turn()

    def handle_disconnection(self):
        logging.info(f"{request.sid} disconnected. Resetting game.")
        self.reset_game()
        self.broadcast_updated_game(
            "step_proceeded",
            console_message=f"{request.sid} disconnected. Resetting game.",
        )
        self.players.pop(request.sid)
        return False

    def init_handler(self):
        return render_template(
            self.template_name,
            deck=self.deck.deck,
            num_players=self.num_players,
            isyourturn=True,
        )

    @staticmethod
    def parse_message(message):
        return SocketMessage(**message)

    def ismyturn(self, whoami):
        print(f"Current is: {self.current_turn} players: {self.players}")
        return self.current_turn == self.players[whoami]

    def broadcast_updated_game(self, emit_handler="message", console_message=None):
        print(f"Broadcasting: {self.players.keys()}")
        # for player in self.players.keys():

        logging.info(f"Player {request.sid} {self.ismyturn(request.sid)}")
        deck_body = self.deck.render_template(
            self.ismyturn(request.sid), self.num_players, request.sid
        )

        sm = SocketMessage(
            socket_context=SocketContext(
                **{"whoami": request.sid, "num_players": self.num_players}
            ),
            game_context=GameContext(
                **{
                    "whoami_sign": self.players[request.sid],
                    "deck_body": deck_body,
                    "console_message": console_message,
                    "last_turn_by": self.players_inv[self.current_turn],
                }
            ),
        )

        logging.info(f"Sending to {emit_handler} || {request.sid} ")
        emit(emit_handler, sm.dict(), broadcast=True)

    def handle_connection_established(self, message):
        message = self.parse_message(message)
        if len(self.players) >= 2:
            pass
        else:
            logging.info(f"received message: {message}")
            self.players[message.socket_context.whoami] = (
                "X" if len(self.players) == 0 else "O"
            )

        console_message = ""
        if self.num_players == 1:
            console_message = (
                "Waiting for other players. Or start playing for AI connecting."
            )

        self.broadcast_updated_game(
            "connection_established", console_message=console_message
        )

    def change_current_turn(self):
        if self.current_turn:
            if self.deck.check_victory(self.current_turn):
                return True
        self.current_turn = next(self.turn_generator)

    def handle_button_clicked(self, message):
        if self.num_players == 1:
            logging.info("Staring AI session")
            self.ai_enabled = True

        message = self.parse_message(message)
        logging.info(f"Button with id: {message.socket_context.button_id} was clicked.")

        if self.players[message.socket_context.whoami] == self.current_turn:
            idx = self.convert_jinja_to_deck(message.socket_context.button_id)
            self.deck.make_step(
                self.players[message.socket_context.whoami], coordinates=idx
            )
            victory = self.change_current_turn()
            self.deck.render_console()

            if self.ai_enabled:
                action = self.ai_agent(
                    torch.Tensor(self.deck.ohe_deck_inverted)
                ).argmax()
                self.deck.make_step("O", elem_index=action)
                self.change_current_turn()
                self.deck.render_console()

        else:
            logging.info("Illigal move")

        self.broadcast_updated_game("step_proceeded", console_message="")


app = Game(__name__, (3, 3))
app.config["SECRET_KEY"] = "secret!"


if __name__ == "__main__":
    app.socket_io.run(app)
