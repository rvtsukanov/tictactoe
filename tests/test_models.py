from models import Deck


def test_make_random_step():
    d = Deck((3, 3))
    d.make_step("X", (0, 0))
    d.make_step("O", (1, 1))
    d.make_step("O", (2, 2))
    d.make_step("X", (1, 2))
    d.make_step("X", (2, 1))

    d.render_console()
    d.make_random_step("X")
    d.render_console()

    assert True


def test_deserialize():
    d = Deck()

    d_new = Deck()
    d_new.deserialize(d.serialize())

    assert d_new.deck == d.deck
