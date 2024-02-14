import numpy as np


def getFirstSetBitPos(n)->int:
    if n == 0:
        return 0
    return int(np.log2(n & -n) + 1)


def setBitNumber(n)->int:
    if n == 0:
        return 0

    k = int(np.log2(n))

    return 1 << k
