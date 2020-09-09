import sympy
from helpers import *

def ToMemLayout(*args):
    if len(args) == 1:
        return type(args[0])(*ToMemLayout(args[0].i, args[0].j, args[0].k))
    if len(args) == 3:
        i,j,k = args
        #return j,k,i # CPU
        return k,j,i # GPU
        #return i,j,k # Trivial

def ToStridePolicy3D(I, J, K):
    return I, J, K
    # # To memory layout
    # I, J, K = ToMemLayout(I, J, K)

    # # Adapt lowest order memory access
    # if K is not None:
    #     K = 32 * sympy.ceiling(K / 32)

    # # Back from memory layout
    # for _ in range(5):
    #     I, J, K = ToMemLayout(I, J, K)
    
    # return I, J, K
