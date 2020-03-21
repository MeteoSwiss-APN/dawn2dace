import unittest
import numpy
import sys
import os
from IndexHandling import *
from Intermediates import Int3D

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
        return arr.transpose(list(ToMemLayout(Int3D(0, 1, 2)))).copy()
    if len(arr.shape) == 2:
        return arr.transpose([x for x in ToMemLayout(Int3D(0, 1, None)) if x is not None]).copy()
    raise TypeError("Expected 2D or 3D array.")


def Iota(I, J, K = None, offset = 0):
    strides = Pad(Any3D(I, J, K))
    if strides.k is None:
        return numpy.arange(offset, offset + strides.i * strides.j).astype(dace.float64.type).reshape(strides.i, strides.j)
    else:
        strides.k = strides.k + 1
        return numpy.arange(offset, offset + strides.i * strides.j * strides.k).astype(dace.float64.type).reshape(strides.i, strides.j, strides.k)

def Zeros(I, J, K = None):
    strides = Pad(Any3D(I, J, K))
    if strides.k is None:
        return numpy.zeros(shape=(strides.i, strides.j), dtype=dace.float64.type)
    else:
        strides.k = strides.k + 1
        return numpy.zeros(shape=(strides.i, strides.j, strides.k), dtype=dace.float64.type)

    
class LegalSDFG:
    def test_1_file_exists(self):
        self.assertIsNotNone(read_file(self.file_name + ".0.iir"))

    def test_2_sdfg_is_valid(self):
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.validate()
        self.assertTrue(sdfg.is_valid())

class Asserts(unittest.TestCase):
    def assertEqual(self, expected, received):
        self.assertTrue(
            (expected == received).all(),
            "\nExpected:\n{}\nReceived:\n{}\nDifference:\n{}".format(expected, received, received - expected)
        )

    def assertIsClose(self, expected, received, rtol=1e-8):
        self.assertTrue(
            numpy.isclose(expected, received, rtol=rtol).all(),
            "\nExpected:\n{}\nReceived:\n{}\nDifference:\n{}".format(expected, received, received - expected)
        )