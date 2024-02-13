from binmanipulation import *


def test_getFirstSetBitPoswith12():
    assert getFirstSetBitPos(12) == 3


def test_getFirstSetBitPoswith64():
    assert getFirstSetBitPos(64) == 7


def test_getFirstSetBitPoswith0():
    assert getFirstSetBitPos(0) == 0


def test_getFirstSetBitPoswith1():
    assert getFirstSetBitPos(~223) == 6
