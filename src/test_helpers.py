import unittest
import numpy
import sys
import os
import math
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

class Dim:
    def __init__(self, domain_sizes:list, strides:list, total_size:int):
        self.I, self.J, self.K = domain_sizes # for bounds checking
        self.strides = strides # for indexed accesses
        self.shape = [x for x in domain_sizes if x] # for bounds checking
        self.total_size = total_size # for memory allocation

def ToMemoryLayout(input:list, memory_layout:str='ijk'):
    return [input['ijk'.find(memory_layout[i])] for i in range(3)]

class Dimensions:
    def __init__(self, domain_sizes:list, memory_sizes:list, memory_layout:str='jki', halo=0):
        self.I, self.J, self.K = domain_sizes
        self.halo = halo

        I,J,K = domain_sizes # helpers
        i,j,k = memory_sizes # helpers
        K += 1 # add one for staggering
        assert i >= I
        assert j >= J
        assert k >= K
        
        strides_ij = [x for x in ToMemoryLayout([j,1,0]) if x]

        self.ijk = Dim(ToMemoryLayout([ I  , J  , K  ]),  strides=ToMemoryLayout([j*k,k,1]), total_size=i*j*k)
        self.ij  = Dim(ToMemoryLayout([ I  , J  ,None]),  strides=strides_ij, total_size=i*j)
        self.i   = Dim(ToMemoryLayout([ I  ,None,None]),  strides=[1], total_size=i)
        self.j   = Dim(ToMemoryLayout([None, J  ,None]),  strides=[1], total_size=j)
        self.k   = Dim(ToMemoryLayout([None,None, K  ]),  strides=[1], total_size=k)

    def ProgramArguments(self):
        return {
            'I' : numpy.int32(self.I),
            'J' : numpy.int32(self.J),
            'K' : numpy.int32(self.K),
            'halo' : numpy.int32(self.halo),
            'IJK_stride_I' : numpy.int32(self.ijk.strides[0]),
            'IJK_stride_J' : numpy.int32(self.ijk.strides[1]),
            'IJK_stride_K' : numpy.int32(self.ijk.strides[2]),
            'IJK_total_size' : numpy.int32(self.ijk.total_size),
            'IJ_stride_I' : numpy.int32(self.ij.strides[0]),
            'IJ_stride_J' : numpy.int32(self.ij.strides[1]),
            'IJ_total_size' : numpy.int32(self.ij.total_size),
            'I_total_size' : numpy.int32(self.i.total_size),
            'J_total_size' : numpy.int32(self.j.total_size),
            'K_total_size' : numpy.int32(self.k.total_size)
        }

def Zeros(dim:Dim):
    arr = numpy.zeros(dim.total_size, dtype=dace.float64.type)
    byte_strides = [s * dace.float64.bytes for s in dim.strides]
    return as_strided(arr, shape=dim.shape, strides=byte_strides)

def Iota(dim:Dim, offset=0):
    arr = numpy.arange(offset, offset + dim.total_size).astype(dace.float64.type)
    byte_strides = [s * dace.float64.bytes for s in dim.strides]
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