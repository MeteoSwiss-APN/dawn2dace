import sympy

def ToMemLayout(i, j, k):
    return j, k, i # Memory layout

def ToStridePolicy(lowest_order_dimension):
    return 8 * sympy.ceiling(lowest_order_dimension / 8)

def ToStridePolicy3D(I, J, K):
    return ToStridePolicy(I), J, K # Memory layout

class Index3D:
    def __init__(self, i:int, j:int, k:int):
        self.i = i
        self.j = j
        self.k = k
