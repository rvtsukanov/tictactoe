import pytest
from models import Deck
import random


@pytest.fixture
def deck_no_victory():
    d = Deck((3, 3))
    d.make_step("X", (0, 0))
    d.make_step("O", (0, 1))
    d.make_step("X", (0, 2))
    d.make_step("O", (1, 0))
    d.make_step("O", (1, 1))
    d.make_step("X", (1, 2))
    d.make_step("O", (2, 0))
    d.make_step("X", (2, 1))
    d.make_step("O", (2, 2))
    return d


@pytest.fixture
def deck_x_win():
    d = Deck((2, 2))
    d.make_step("X", elem_index=0)
    d.make_step("X", elem_index=3)

    return d


@pytest.fixture
def dec_hor_victory():
    d = Deck((3, 3))
    row_idx = random.randint(0, len(d.deck[0]) - 1)
    for i in range(len(d.deck[0])):
        d.make_step("X", (row_idx, i))
    d.render_console()
    return d


@pytest.fixture
def dec_vert_victory():
    d = Deck((3, 3))
    vert_idx = random.randint(0, len(d.deck[0]) - 1)
    for i in range(len(d.deck[0])):
        d.make_step("X", (i, vert_idx))
    d.render_console()
    return d


@pytest.fixture
def dec_diag_victory_1():
    d = Deck((3, 3))
    d.make_step("X", (0, 0))
    d.make_step("X", (1, 1))
    d.make_step("X", (2, 2))
    return d


@pytest.fixture
def dec_diag_victory_2():
    d = Deck((3, 3))
    d.make_step("X", (0, 2))
    d.make_step("X", (1, 1))
    d.make_step("X", (2, 0))
    d.render_console()
    return d


def test_diag_1(dec_diag_victory_1):
    assert dec_diag_victory_1.check_victory()


def test_diag_2(dec_diag_victory_2):
    assert dec_diag_victory_2.check_victory()


def test_hor_victory(dec_hor_victory):
    assert dec_hor_victory.check_victory()


def test_no_victory(deck_no_victory):
    assert not deck_no_victory.check_victory()


def test_vert_victory(dec_vert_victory):
    assert dec_vert_victory.check_victory()


def test_check_game_over(deck_no_victory):
    deck_no_victory.render_console()
    assert deck_no_victory.check_game_over()


def test_check_game_over_false(deck_no_victory):
    deck_no_victory.deck[0][0] = deck_no_victory.none_sign
    deck_no_victory.render_console()
    assert not deck_no_victory.check_game_over()


def test_check_game_over_with_victory(deck_no_victory):
    deck_no_victory.deck[0][0] = deck_no_victory.none_sign
    deck_no_victory.deck[2][2] = deck_no_victory.x_sign
    deck_no_victory.render_console()
    assert deck_no_victory.check_game_over()


def test_x_win(deck_x_win):
    assert deck_x_win.check_victory("X")
