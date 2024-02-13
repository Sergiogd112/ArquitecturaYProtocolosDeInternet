import numpy as np
def getFirstSetBitPos(n):
    if n==0:
        return 0
    return int(np.log2(n & -n) + 1)