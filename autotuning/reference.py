import dace
import numpy
import math
import operator
import sys
from numpy.lib.stride_tricks import as_strided
from functools import reduce

def prod(iterable):
    return reduce(operator.mul, iterable, 1)

def lap2D(data, i, j, k, plus=None, minus=None):
    if (plus is None) and (minus is None):
        return data[i-1,j,k] + data[i+1,j,k] - 2.0 * data[i,j,k] \
            + (data[i,j+1,k] - data[i,j,k]) \
            + (data[i,j-1,k] - data[i,j,k])

    return data[i-1,j,k] + data[i+1,j,k] - 2.0 * data[i,j,k] \
        + plus[j] * (data[i,j+1,k] - data[i,j,k]) \
        + minus[j] * (data[i,j-1,k] - data[i,j,k])


def diffusive_flux_x(lap, data, i, j, k):
    flx = lap[i+1,j,k] - lap[i,j,k]
    return 0.0 if (flx * (data[i+1,j,k] - data[i,j,k])) > 0.0 else flx

def diffusive_flux_y(lap, data, crlato, i, j, k):
    fly = crlato[j] * (lap[i,j+1,k] - lap[i,j,k])
    return 0.0 if (fly * (data[i,j+1,k] - data[i,j,k])) > 0.0 else fly

def type2(data, crlato, crlatu, hdmask, dim, halo=None):
    halo = halo or dim.halo
    lap = Zeros(dim.ijk)
    for i in range(1, dim.I-1):
        for j in range(1, dim.J-1):
            for k in range(0, dim.K):
                lap[i,j,k] = lap2D(data, i, j, k, crlato, crlatu)

    out = Zeros(dim.ijk)
    for i in range(halo, dim.I-halo):
        for j in range(halo, dim.J-halo):
            for k in range(0, dim.K):
                delta_flux_x = diffusive_flux_x(lap, data, i, j, k) - diffusive_flux_x(lap, data, i-1, j, k)
                delta_flux_y = diffusive_flux_y(lap, data, crlato, i, j, k) - diffusive_flux_y(lap, data, crlato, i, j-1, k)
                out[i,j,k] = data[i,j,k] - hdmask[i,j,k] * (delta_flux_x + delta_flux_y)
    return out

def smag(u, v, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0, dim):
    eddlon = 5729.58
    eddlat = 5729.58
    T_sqr_s = Zeros(dim.ijk)
    for i in range(1, dim.I):
        for j in range(1, dim.J):
            for k in range(0, dim.K):
                frac_1_dx = acrlat0[j] * eddlon
                frac_1_dy = eddlat / 6371.229e3

                T_s = (v[i,j-1,k] - v[i,j,k]) * frac_1_dy - (u[i-1,j,k] - u[i,j,k]) * frac_1_dx
                T_sqr_s[i,j,k] = T_s * T_s

    S_sqr_uv = Zeros(dim.ijk)
    for i in range(0, dim.I-1):
        for j in range(0, dim.J-1):
            for k in range(0, dim.K):
                frac_1_dx = acrlat0[j] * eddlon
                frac_1_dy = eddlat / 6371.229e3

                S_uv = (u[i,j+1,k] - u[i,j,k]) * frac_1_dy - (v[i+1,j,k] - v[i,j,k]) * frac_1_dx
                S_sqr_uv[i,j,k] = S_uv * S_uv

    u_out = Zeros(dim.ijk)
    v_out = Zeros(dim.ijk)
    for i in range(dim.halo, dim.I-dim.halo):
        for j in range(dim.halo, dim.J-dim.halo):
            for k in range(0, dim.K):
                weight_smag = 0.5
                tau_smag = 0.3
                hdweight = weight_smag * hdmask[i,j,k]

                smag_u = tau_smag * numpy.sqrt(0.5 * (T_sqr_s[i,j,k] + T_sqr_s[i+1,j,k]) + 0.5 * (S_sqr_uv[i,j,k] + S_sqr_uv[i,j-1,k])) - hdweight
                smag_u = min(0.5, max(0.0, smag_u))
                u_out[i,j,k] = u[i,j,k] + smag_u * lap2D(u, i, j, k, crlato, crlatu)

                smag_v = tau_smag * numpy.sqrt(0.5 * (T_sqr_s[i,j,k] + T_sqr_s[i,j+1,k]) + 0.5 * (S_sqr_uv[i,j,k] + S_sqr_uv[i-1,j,k])) - hdweight
                smag_v = min(0.5, max(0.0, smag_v))
                v_out[i,j,k] = v[i,j,k] + smag_v * lap2D(v, i, j, k, crlavo, crlavu)
    return u_out, v_out

class Dim:
    def __init__(self, domain_sizes:list, strides:list, total_size:int):
        """
        domain_sizes in domain layout
        strides in memory layout
        """
        self.I, self.J, self.K = domain_sizes # for loop ranges
        self.strides = strides # for indexed access
        self.shape = [x for x in domain_sizes if x] # for bounds checking
        self.total_size = total_size # for memory allocation

def ToMemoryLayout(input, memory_layout):
    memory_layout = list(memory_layout)
    sorted_order = ''.join(sorted(memory_layout))
    return [input[sorted_order.find(x)] for x in memory_layout]

class Dimensions:
    def __init__(self, domain_sizes, memory_sizes, memory_layout, halo=0):
        """
        domain_sizes in domain layout (I,J,K): Logical size of each dimension. Used for bounds checking.
        memory_sizes in domain layout (I,J,K): Number of elements in memory for each dimension. Padding is done with this.
        memory_layout in C-array notation. The right most is contiguous. Must contain a permutation of 'ijk'.
        """

        self.I, self.J, self.K = domain_sizes
        self.halo = halo

        I,J,K = domain_sizes # helpers
        i,j,k = memory_sizes # helpers
        assert i >= I
        assert j >= J
        assert k >= K

        mlms = ToMemoryLayout([i,j,k], memory_layout) # Memory Layouted Memory Sizes
        mlms = mlms[1:] + [1] # removes first element and appends 1.
        strides_ijk = [prod(mlms[memory_layout.find(x):]) for x in list('ijk')]

        ij_memory_layout = memory_layout.replace('k', '')
        mlms = ToMemoryLayout([i,j], ij_memory_layout) # memory layouted memory sizes
        mlms = mlms[1:] + [1] # removes first element and appends 1.
        strides_ij = [prod(mlms[ij_memory_layout.find(x):]) for x in list('ij')]

        self.ijk = Dim([ I  , J  , K  ],  strides=strides_ijk, total_size=i*j*k)
        self.ij  = Dim([ I  , J  ,None],  strides=strides_ij, total_size=i*j)
        self.i   = Dim([ I  ,None,None],  strides=[1], total_size=i)
        self.j   = Dim([None, J  ,None],  strides=[1], total_size=j)
        self.k   = Dim([None,None, K  ],  strides=[1], total_size=k)

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
    arr = numpy.zeros(dim.total_size, dtype=dace.float32.type)
    byte_strides = [s * dace.float32.bytes for s in dim.strides]
    return as_strided(arr, shape=dim.shape, strides=byte_strides)

def Iota(dim:Dim, offset=0):
    arr = numpy.arange(offset, offset + dim.total_size).astype(dace.float32.type)
    byte_strides = [s * dace.float32.bytes for s in dim.strides]
    return as_strided(arr, shape=dim.shape, strides=byte_strides)

def Waves(a, b, c, d, e, f, dim:Dim):
    data = Zeros(dim)
    for i in range(dim.I or 1):
        for j in range(dim.J or 1):
            x = i / (dim.I or 1)
            y = j / (dim.J or 1)
            tmp = a * (b + math.cos(math.pi * (x + c * y)) + math.sin(d * math.pi * (x + e * y))) / f
            for k in range(dim.K or 1):
                index = tuple(idx for idx, size in [(i,dim.I),(j,dim.J),(k,dim.K)] if size)
                data[index] = tmp + k * 0.01
    return data

def assertIsClose(expected, received, name, dim, rtol=1e-5):
    with numpy.printoptions(threshold=sys.maxsize):
        if numpy.isclose(expected, received, rtol=rtol).all():
            print(f"{name} is good!")
        else:
            print(f"{name} is bad!")
            # for i in range(0,dim.I):
            #     for j in range(0,dim.J):
            #         for k in range(0,dim.K):
            #             if received[i,j,k] != expected[i,j,k]:
            #                 print(f"{name}[{i},{j},{k}] ref {expected[i,j,k]}, dace {received[i,j,k]}, diff {received[i,j,k]-expected[i,j,k]}")


def CreateInputData(domain_sizes, memory_layout):
    I,J,K = domain_sizes
    memory_sizes = [I,J,K+1]
    dim = Dimensions(domain_sizes=domain_sizes, memory_sizes=memory_sizes, memory_layout=memory_layout, halo=4)

    u_in = Waves(1.80, 1.20, 0.15, 1.15, 0.20, 1.40, dim.ijk)
    v_in = Waves(1.60, 1.10, 0.09, 1.11, 0.20, 1.40, dim.ijk)
    hdmask = Waves(0.3, 1.22, 0.17, 1.19, 0.20, 1.40, dim.ijk)
    crlavo = Waves(1.65, 1.12, 0.17, 1.19, 0.21, 1.20, dim.j)
    crlavu = Waves(1.50, 1.22, 0.17, 1.19, 0.20, 1.10, dim.j)
    crlato = Waves(1.65, 1.12, 0.17, 1.09, 0.21, 1.20, dim.j)
    crlatu = Waves(1.50, 1.22, 0.17, 1.09, 0.20, 1.10, dim.j)
    acrlat0 = Waves(1.65, 1.22, 0.11, 1.52, 0.42, 1.02, dim.j)
    return u_in, v_in, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0

def HD_type2(domain_sizes, memory_layout, u_in, v_in, w_in, pp_in, hdmask, crlato, crlatu):
    I,J,K = domain_sizes
    memory_sizes = [I,J,K+1]
    dim = Dimensions(domain_sizes=domain_sizes, memory_sizes=memory_sizes, memory_layout=memory_layout, halo=4)

    u_out = type2(u_in, crlato, crlatu, hdmask, dim)
    v_out = type2(v_in, crlato, crlatu, hdmask, dim)
    w_out = type2(w_in, crlato, crlatu, hdmask, dim)
    pp_out = type2(pp_in, crlato, crlatu, hdmask, dim)
    return u_out, v_out, w_out, pp_out

def HD_smag(domain_sizes, memory_layout, u_in, v_in, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0):
    I,J,K = domain_sizes
    memory_sizes = [I,J,K+1]
    dim = Dimensions(domain_sizes=domain_sizes, memory_sizes=memory_sizes, memory_layout=memory_layout, halo=4)

    u_out, v_out = smag(u_in, v_in, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0, dim)
    return u_out, v_out
