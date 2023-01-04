import logging
import itertools
import socket
from constants import HOST, PORT
import threading
import pickle
from enum import Enum
import jinja2
import json
import numpy as np

logging.root.setLevel(logging.INFO)
logging.basicConfig(format="", level=logging.INFO)


class Deck:
    x_sign = "X"
    o_sign = "O"
    none_sign = " "
    player_signs = [x_sign, o_sign]
    all_signs = [x_sign, o_sign, none_sign]
    all_signs_inverted = [o_sign, x_sign, none_sign]

    def __init__(self, size=(3, 3)):
        if size[0] != size[1]:
            raise ValueError("Squared decks only are supported")

        self.size = size
        self.deck = [
            [self.none_sign for _ in range(self.size[0])] for _ in range(self.size[1])
        ]

    @property
    def inv_deck(self):
        return list(zip(*self.deck))

    @property
    def flatted_deck(self):
        return [item for row in self.deck for item in row]

    @property
    def encoded_flatted_deck(self):
        """Only values from all_signs are allowed!"""
        return [self.all_signs.index(item) for item in self.flatted_deck]

    @property
    def inverted_encoded_flatted_deck(self):
        """Only values from all_signs are allowed!"""
        return [self.all_signs_inverted.index(item) for item in self.flatted_deck]

    @property
    def available_actions_map(self):
        return [item == self.none_sign for item in self.flatted_deck]

    @property
    def diag_deck(self):
        lists = []
        for i in range(len(self.deck[0])):
            lists.append(self.deck[i][i])

        inv_lists = []
        for i in range(len(self.inv_deck[0])):
            inv_lists.append(self.inv_deck[i][len(self.inv_deck[0]) - i - 1])

        return [lists, inv_lists]

    def _convert_idx_to_coordinates(self, idx):
        logging.debug(
            f"Got idx: {idx}. Converting into coords: ({idx // self.size[0]}, {idx % self.size[1]})"
        )
        return idx // self.size[0], idx % self.size[1]

    def _convert_coordinates_to_idx(self, coordinates):
        logging.debug(
            f"Got coords: {coordinates}. Converting into idx: {self.size[0] * coordinates[0]} + {coordinates[1]}"
        )
        return self.size[0] * coordinates[0] + coordinates[1]

    def render_console(self):
        logging.info("-" * 10)
        logging.info("\n".join(map(str, self.deck)))

    def make_step(self, whoami, coordinates=None, elem_index=None):
        if coordinates is not None and elem_index is not None:
            raise ValueError(
                "Redefine make_step using only one option: either coord or elem_idx"
            )

        if elem_index is not None:
            coordinates = self._convert_idx_to_coordinates(elem_index)
            logging.debug(f"Convert idx: {elem_index} to coords: {coordinates}")

        if coordinates:
            if self.deck[coordinates[0]][coordinates[1]] == self.none_sign:
                self.deck[coordinates[0]][coordinates[1]] = whoami
                return self.check_victory(whoami), self.check_game_over(), False
            else:
                # Deck position is violated -> penalty!
                return False, True, True

    def make_random_step(self, whoami):
        import random

        idx = []
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                if self.deck[i][j] == self.none_sign:
                    idx.append((i, j))
        if idx:
            chosen_idx = idx[random.randint(0, len(idx) - 1)]
            self.deck[chosen_idx[0]][chosen_idx[1]] = whoami
            return self.check_victory(whoami), self.check_game_over(), False

    @property
    def ohe_deck(self):
        return np.squeeze(
            np.eye(len(self.all_signs))[self.encoded_flatted_deck].reshape(-1)
        )

    @property
    def ohe_deck_inverted(self):
        return np.squeeze(
            np.eye(len(self.all_signs))[self.inverted_encoded_flatted_deck].reshape(-1)
        )

    @staticmethod
    def check_items_in_list(lst, target):
        return lst.count(target) == len(lst)

    def check_victory(self, whoami=None):
        """
        :param whoami: if None - check any victory
        :return:
        """
        victory_flg = False

        if whoami is None:
            avail_signs = [self.x_sign, self.o_sign]
        else:
            avail_signs = [self.x_sign] * (whoami == self.x_sign) + [self.o_sign] * (
                whoami == self.o_sign
            )

        for sign, deck in itertools.product(
            avail_signs, [self.deck, self.inv_deck, self.diag_deck]
        ):
            victory_flg |= any([self.check_items_in_list(row, sign) for row in deck])

        return victory_flg

    def check_game_over(self):
        return self.check_victory() or not (self.none_sign in self.flatted_deck)

    def render_template(self, isyourturn, num_players, whoami):
        def render_jinja_html(
            template_path,
            file_name,
            isyourturn=isyourturn,
            num_players=num_players,
            whoami=whoami,
        ):
            return (
                jinja2.Environment(loader=jinja2.FileSystemLoader(template_path + "/"))
                .get_template(file_name)
                .render(
                    deck=self.deck,
                    isyourturn=isyourturn,
                    num_players=num_players,
                    whoami=whoami,
                )
            )

        return render_jinja_html(
            "./templates",
            "subindex.html",
            isyourturn=isyourturn,
            num_players=num_players,
            whoami=whoami,
        )

    def serialize(self):
        return json.dumps(self.__dict__)

    def deserialize(self, json_file):
        attrs = json.loads(json_file)
        self.deck = attrs["deck"]
        self.size = attrs["size"]


class MessageStatus(Enum):
    # NEW_STATE = 0
    FAIL = 1
    NEW_GAME = 2
    STEP_REQ = 3
    VICTORY = 4


class Message:
    def __init__(self, deck, message_status):
        self.deck = deck
        self.message_status = message_status


class Game:
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.init_game_deck()
        self.players_connected = []
        self.last_player_id = None

    def init_game_deck(self, **kwargs):
        self.deck = Deck(**kwargs)

    def one_thread(self, conn, addr):
        logging.info(conn)
        logging.info(addr)

        msg = conn.recv(86400)
        data = pickle.loads(msg)

        if isinstance(data.message_status, MessageStatus.NEW_GAME):
            self.init_game_deck()
            self.socket.sendall("New game started!".encode("utf-8"))
        logging.info(msg)

    def run(self):
        self.socket.listen()
        while True:
            conn, addr = self.socket.accept()
            self.players_connected.append(addr)
            threading.Thread(target=self.one_thread, args=(conn, addr)).start()


class Player:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT))
        logging.info("Connected to a server.")
        self.deck = Deck()

    def request_to_start_new_game(self):
        data = Message(self.deck, MessageStatus.NEW_GAME)
        self.socket.send(pickle.dumps(data))

    def run(self):
        while True:
            data = self.socket.recv(100000)
