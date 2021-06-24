import unittest
import numpy
import sys
import os
import math
from helpers import *
from numpy.lib.stride_tricks import as_strided
from dace.transformation.interstate import InlineSDFG
from dace.transformation.dataflow import MapFission, MapCollapse, MapFusion, MapExpansion, MapToForLoop, TrivialMapElimination, TrivialMapRangeElimination

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

def Zeros(dim:Dim, floattype=dace.float64):
    arr = numpy.zeros(dim.total_size, dtype=floattype.type)
    byte_strides = [s * floattype.bytes for s in dim.strides]
    return as_strided(arr, shape=dim.shape, strides=byte_strides)

def Iota(dim:Dim, offset=0, floattype=dace.float64):
    arr = numpy.arange(offset, offset + dim.total_size).astype(floattype.type)
    byte_strides = [s * floattype.bytes for s in dim.strides]
    return as_strided(arr, shape=dim.shape, strides=byte_strides)

def Waves(a, b, c, d, e, f, dim:Dim):
    data = Zeros(dim)
    for i in range(dim.I or 1):
        for j in range(dim.J or 1):
            for k in range(dim.K or 1):
                index = tuple(index for index, size in [(i,dim.I),(j,dim.J),(k,dim.K)] if size)
                x = i / (dim.I or 1)
                y = j / (dim.J or 1)
                data[index] = k * 0.01 + a * (b + math.cos(math.pi * (x + c * y)) + math.sin(d * math.pi * (x + e * y))) / f
    return data
    
class LegalSDFG:
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