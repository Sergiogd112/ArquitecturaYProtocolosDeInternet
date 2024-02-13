from binmanipulation import *


def test_getFirstSetBitPoswith12():
    assert getFirstSetBitPos(12) == 3


def test_getFirstSetBitPoswith64():
    assert getFirstSetBitPos(64) == 7


def test_getFirstSetBitPoswith0():
    assert getFirstSetBitPos(0) == 0


def test_getFirstSetBitPoswith1():
    assert getFirstSetBitPos(~223) == 6

def test_setBitNumberwith12():
    assert setBitNumber(12) == 8
def test_setBitNumberwith64():
    assert setBitNumber(64) == 64
def test_setBitNumberwith0():
    assert setBitNumber(0) == 0
def test_setBitNumberwith1():
    assert setBitNumber(1) == 1
def test_setBitNumberwith2():
    assert setBitNumber(2) == 2
def test_setBitNumberwith3():
    assert setBitNumber(3) == 2