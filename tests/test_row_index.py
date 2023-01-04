import pytest
from models import Deck
import random
import logging


def test_coord_to_idx():
    d = Deck((3, 3))

    max_row, max_col = len(d.deck), len(d.deck)
    row = random.randint(0, max_row - 1)
    col = random.randint(0, max_col - 1)

    d.make_step("X", coordinates=(row, col))
    d.render_console()

    d_idx = Deck((3, 3))

    logging.info(
        f"Index is: {d_idx._convert_coordinates_to_idx((row, col))}; coords are: {row, col}"
    )
    d_idx.make_step("X", elem_index=d_idx._convert_coordinates_to_idx((row, col)))
    d_idx.render_console()

    assert d.deck == d_idx.deck


@pytest.mark.parametrize(("coords", "idx"), (((1, 1), 4), ((0, 0), 0)))
def test_idx_to_coord(coords, idx):
    d = Deck((3, 3))
    d.make_step("X", elem_index=idx)

    d2 = Deck((3, 3))
    d2.make_step("X", coordinates=coords)

    assert d.deck == d2.deck


def test_flatten_conv():
    assert Deck((2, 2)).flatted_deck == ["."] * 4


def test_encodings():
    d = Deck((2, 2))
    d.make_step("X", elem_index=0)
    d.make_step("O", elem_index=3)

    d.render_console()

    assert d.encoded_flatted_deck == [0, 2, 2, 1]
