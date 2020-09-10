import unittest
import numpy
import sys
import os
import math
from IndexHandling import *
from dace.transformation.interstate import InlineSDFG

# This is a workaround for a bug in vscode. Apparently it ignores PYTHONPATH. (6.Nov 2019)
sys.path.append(os.path.relpath("build/gen/iir_specification"))
sys.path.append(os.path.relpath("../dace"))
sys.path.append(os.path.relpath("../stencilflow"))

import dawn2dace
import dace

def read_file(file_name):
    with open("gen/" + file_name, "rb") as f:
        return f.read() # IIR as binary str.
    return None

def get_sdfg(file_name):
    iir = read_file(file_name)
    return dawn2dace.IIR_str_to_SDFG(iir)

def Transpose(arr):
    if len(arr.shape) == 3:
        return arr.transpose(list(ToMemLayout(0, 1, 2))).copy()
    if len(arr.shape) == 2:
        return arr.transpose([x for x in ToMemLayout(0, 1, None) if x is not None]).copy()
    return arr

class Dim:
    def __init__(self, I, J, K, stride_i, stride_j, stride_k, total_size):
        self.I = I # is used for bounds checking
        self.J = J # is used for bounds checking
        self.K = K # is used for bounds checking
        self.stride_i = stride_i
        self.stride_j = stride_j
        self.stride_k = stride_k
        self.shape = [x for x in [I,J,K] if x is not None] # is used for bounds checking
        self.total_size = total_size # is used for memory allocation

class Dimensions:
    def __init__(self, I, J, K):
        self.I = I
        self.J = J
        self.K = K
        self.ijk = Dim(I,J,K, J*K,K,1, I*J*K)
        self.ij = Dim(I,J,None, J,1,0, I*J)
        self.ik = Dim(I,None,K, K,0,1, I*K)
        self.jk = Dim(None,J,K, 0,K,1, J*K)
        self.i = Dim(I,None,None, 1,0,0, I)
        self.j = Dim(None,J,None, 0,1,0, J)
        self.k = Dim(None,None,K, 0,0,1, K)

def Zeros(dim:Dim):
    return numpy.zeros(shape=dim.shape, dtype=dace.float64.type)

def Iota(dim:Dim, offset=0):
    size = (dim.I or 1) * (dim.J or 1) * (dim.K or 1)
    return numpy.arange(offset, offset + size).astype(dace.float64.type).reshape(dim.shape)

def Waves(a, b, c, d, e, f, dim:Dim):
    data = Zeros(dim)
    for i in range(dim.I or 1):
        for j in range(dim.J or 1):
            for k in range(dim.K or 1):
                index = tuple(index for index, size in [(i,dim.I),(j,dim.J),(k,dim.K)] if size is not None)
                x = i / (dim.I or 1)
                y = j / (dim.J or 1)
                data[index] = k * 0.01 + a * (b + math.cos(math.pi * (x + c * y)) + math.sin(d * math.pi * (x + e * y))) / f
    return data
    
class LegalSDFG:
    # def test_1_file_exists(self):
    #     self.assertIsNotNone(read_file(self.__class__.__name__ + ".iir"))

    def test_2_sdfg_is_valid(self):
        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        self.assertTrue(sdfg.is_valid())

class Asserts(unittest.TestCase):
    def assertEqual(self, expected, received):
        with numpy.printoptions(threshold=sys.maxsize):
            self.assertTrue(
                (expected == received).all(),
                "\nExpected:\n{}\nReceived:\n{}\nDifference:\n{}".format(expected, received, received - expected)
            )

    def assertIsClose(self, expected, received, rtol=1e-10):
        with numpy.printoptions(threshold=sys.maxsize):
            self.assertTrue(
                numpy.isclose(expected, received, rtol=rtol).all(),
                "\nExpected:\n{}\nReceived:\n{}\nDifference:\n{}".format(expected, received, received - expected)
            )