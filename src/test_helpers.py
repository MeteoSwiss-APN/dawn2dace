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


def Iota(I=None, J=None, K=None, offset=0):
    I, J, K = ToStridePolicy3D(I, J, K)
    if K is not None:
        K += 1
    size = (1 if I is None else I) * (1 if J is None else J) * (1 if K is None else K)
    shape = [x for x in [I,J,K] if x is not None]
    return numpy.arange(offset, offset + size).astype(dace.float64.type).reshape(*shape)

def Zeros(I=None, J=None, K=None):
    I, J, K = ToStridePolicy3D(I, J, K)
    if K is not None:
        K += 1
    shape = [x for x in [I,J,K] if x is not None]
    return numpy.zeros(shape=tuple(shape), dtype=dace.float64.type)

def Waves(a, b, c, d, e, f, I=None, J=None, K=None):
    data = Zeros(I,J,K)
    for i in range(1 if I is None else I):
        for j in range(1 if J is None else J):
            for k in range(1 if K is None else K):
                index = tuple(index for index, size in [(i,I),(j,J),(k,K)] if size is not None)
                x = i / (1 if I is None else I)
                y = j / (1 if J is None else J)
                data[index] = k * 0.01 + a * (b + math.cos(math.pi * (x + c * y)) + math.sin(d * math.pi * (x + e * y))) / f
    return data
    
class LegalSDFG:
    # def test_1_file_exists(self):
    #     self.assertIsNotNone(read_file(self.__class__.__name__ + ".iir"))

    def test_2_sdfg_is_valid(self):
        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations()
        sdfg.validate()
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