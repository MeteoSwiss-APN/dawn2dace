import copy
import numpy
from functools import reduce
from operator import mul

class Any3D:
    "Holds 3 objects in members i,j,k."

    def __init__(self, i, j, k):
        self.i = i
        self.j = j
        self.k = k

    def __iter__(self):
        return (x for x in [self.i, self.j, self.k])

    def __hash__(self):
        return hash(self.__iter__())

    def __eq__(self, o) -> bool:
        return (self.i == o.i) and (self.j == o.j) and (self.k == o.k)

    def __ne__(self, o) -> bool:
        return not self == o

    def __str__(self) -> str:
        return ', '.join([str(self.i), str(self.j), str(self.k)])

    def to_tuple(self) -> tuple:
        return (self.i, self.j, self.k)


class Bool3D(Any3D):
    "Holds 3 bools in members i,j,k."

    def __init__(self, i:bool, j:bool, k:bool):
        Any3D.__init__(self, i, j, k)

    @classmethod
    def Or(cls, bools) -> bool:
        # Make list without None
        bools = [x for x in bools if x is not None]
        if len(bools) == 0:
            return None
        ret = Bool3D(False, False, False)
        for x in bools:
            ret.i |= x.i
            ret.j |= x.j
            ret.k |= x.k
        return ret


class HalfOpenInterval:
    """ An interval that does not includ its upper boundary [lower, upper). """

    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def __str__(self) -> str:
        return "{}:{}".format(self.lower, self.upper)

    def __eq__(self, o) -> bool:
        return self.lower == o.lower and self.upper == o.upper

    def __ne__(self, o) -> bool:
        return not self == o

    def __add__(self, o):
        return HalfOpenInterval(self.lower + o, self.upper + o)

    def __sub__(self, o):
        return HalfOpenInterval(self.lower - o, self.upper - o)

    def __hash__(self):
        return hash(self.__dict__.values())

    def offset(self, offset:int):
        self.lower += offset
        self.upper += offset
        return self

    def to_closed_interval(self):
        return ClosedInterval(self.lower, self.upper - 1)

    def range(self):
        return range(self.lower, self.upper)


class ClosedInterval:
    """ An interval that includes its boundaries [lower, upper]. """

    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def __str__(self) -> str:
        return "{}..{}".format(self.lower, self.upper)

    def __eq__(self, o) -> bool:
        return self.lower == o.lower and self.upper == o.upper

    def __ne__(self, o) -> bool:
        return not self == o

    def __add__(self, o):
        return ClosedInterval(self.lower + o.lower, self.upper + o.upper)

    def __sub__(self, o):
        return ClosedInterval(self.lower - o.lower, self.upper - o.upper)

    def __hash__(self):
        return hash(self.__dict__.values())

    def contains(self, o):
        if isinstance(o, ClosedInterval):
            return self.contains(o.lower) and self.contains(o.upper)
        else:
            return self.lower <= o <= self.upper

    def exclude(self, o):
        assert not o.contains(self)
        
        if self.contains(o.lower):
            self.upper = o.lower - 1
        elif self.contains(o.upper):
            self.lower = o.upper + 1

    def offset(self, offset:int):
        self.lower += offset
        self.upper += offset
        return self

    def to_halfopen_interval(self):
        return HalfOpenInterval(self.lower, self.upper + 1)

    def range(self):
        return range(self.lower, self.upper + 1)

    def IsSingleton(self):
        return self.lower == self.upper

def HalfOpenIntervalStr(interval) -> str:
    if isinstance(interval, HalfOpenInterval):
        return str(interval)
    if isinstance(interval, ClosedInterval):
        return str(interval.to_halfopen_interval())


class ClosedInterval3D(Any3D):
    def __init__(self, *args):
        """
        Requires input of 'i_lower, i_upper, j_lower, j_upper, k_lower, k_upper'
        or 'i:ClosedInterval, j:ClosedInterval, k:ClosedInterval'.
        """
        if len(args) == 3:
            Any3D.__init__(self, args[0], args[1], args[2])
        if len(args) == 6:
            Any3D.__init__(self,
                ClosedInterval(args[0], args[1]),
                ClosedInterval(args[2], args[3]),
                ClosedInterval(args[4], args[5]),
            )

    def __add__(self, o):
        return ClosedInterval3D(
            self.i.lower + o.i.lower, self.i.upper + o.i.upper,
            self.j.lower + o.j.lower, self.j.upper + o.j.upper,
            self.k.lower + o.k.lower, self.k.upper + o.k.upper)

    def __sub__(self, o):
        return ClosedInterval3D(
            self.i.lower - o.i.lower, self.i.upper - o.i.upper,
            self.j.lower - o.j.lower, self.j.upper - o.j.upper,
            self.k.lower - o.k.lower, self.k.upper - o.k.upper)

    def contains(self, o):
        return self.i.contains(o.i) and self.j.contains(o.j) and self.k.contains(o.k)

    def exclude(self, o):
        assert self != o
        if self.i != o.i:
            self.i.exclude(o.i)
        if self.j != o.j:
            self.j.exclude(o.j)
        if self.k != o.k:
            self.k.exclude(o.k)

    def offset(self, i: int = 0, j: int = 0, k: int = 0):
        self.i.offset(i)
        self.j.offset(j)
        self.k.offset(k)
        return self

    def to_6_tuple(self) -> tuple:
        return (str(self.i.lower), str(self.i.upper), str(self.j.lower), str(self.j.upper), str(self.k.lower), str(self.k.upper))

    def range(self):
        for i in self.i.range():
            for j in self.j.range():
                for k in self.k.range():
                    yield i,j,k

    def IsSingleton(self):
        return self.i.IsSingleton() and self.j.IsSingleton() and self.k.IsSingleton()


def Hull(intervals):
    intervals = list(x for x in intervals if x is not None)
    if len(intervals) == 0:
        return None
    if isinstance(intervals[0], ClosedInterval):
        return ClosedInterval(min(x.lower for x in intervals), max(x.upper for x in intervals))
    if isinstance(intervals[0], HalfOpenInterval):
        return HalfOpenInterval(min(x.lower for x in intervals), max(x.upper for x in intervals))
    if isinstance(intervals[0], ClosedInterval3D):
        return ClosedInterval3D(
            min(x.i.lower for x in intervals), max(x.i.upper for x in intervals),
            min(x.j.lower for x in intervals), max(x.j.upper for x in intervals),
            min(x.k.lower for x in intervals), max(x.k.upper for x in intervals)
        )


class SymbolicSum:
    def __init__(self, symbols:list=[], positive:list=None, integer:int=0):
        if positive is None:
            positive = [True for _ in symbols]
        self.symbols = symbols
        self.positive = positive
        self.integer = integer

    def __eq__(self, o):
        if isinstance(o, int):
            return (len(self.symbols) == 0) and (len(self.positive) == 0) and (self.integer == o)
        return (self.symbols == o.symbols) and (self.positive == o.positive) and (self.integer == o.integer)

    def __ne__(self, o):
        return not self == o

    def __hash__(self):
        return hash((self.symbols, self.positive, self.integer))

    def __str__(self):
        symbols = ''
        for s, p in zip(self.symbols, self.positive):
            symbols += ('+' if p else '-') + str(s)

        if symbols.startswith('+'):
            symbols = symbols[1:]

        if self.integer > 0:
            return symbols + '+' + str(self.integer)
        if self.integer < 0:
            return symbols + str(self.integer)
        return symbols

    def __neg__(self):
        return SymbolicSum(copy.deepcopy(self.symbols), [not p for p in self.positive], -self.integer)

    def __add__(self, o):
        if isinstance(o, SymbolicSum):
            return SymbolicSum(
                copy.deepcopy(self.symbols) + copy.deepcopy(o.symbols),
                copy.deepcopy(self.positive) + copy.deepcopy(o.positive),
                self.integer + o.integer)
        if isinstance(o, int):
            return self + SymbolicSum(integer=o)
        if isinstance(o, Symbol):
            return self + SymbolicSum(symbols=[o])

    def __sub__(self, o):
        if isinstance(o, SymbolicSum):
            return SymbolicSum(
                copy.deepcopy(self.symbols) + copy.deepcopy(o.symbols),
                copy.deepcopy(self.positive) + [not x for x in o.positive],
                self.integer - o.integer)
        if isinstance(o, int):
            return self - SymbolicSum(integer=o)
        if isinstance(o, Symbol):
            return self - SymbolicSum(symbols=[o])

    def IsInteger(self):
        return len(self.positive) == 0

    def Eval(self, symbol, value:int):
        if isinstance(symbol, str):
            symbol = Symbol(symbol)

        symbols = []
        positive = []
        sum = 0
        for s, p in zip(self.symbols, self.positive):
            if s == symbol:
                if p:
                    sum += value
                else:
                    sum -= value
            else:
                symbols.append(s)
                positive.append(p)

        self.symbols = symbols
        self.positive = positive
        self.integer += sum
        return self


class Symbol:
    def __init__(self, symbol:str):
        self.symbol = symbol

    def __str__(self):
        return self.symbol

    def __eq__(self, o):
        return self.symbol == o.symbol

    def __ne__(self, o):
        return not self == o

    def __neg__(self):
        return SymbolicSum() - self

    def __add__(self, o):
        return SymbolicSum() + self + o

    def __sub__(self, o):
        return SymbolicSum() + self - o


def FullEval(expr, symbol, value) -> int:
    if isinstance(expr, int):
        return expr
    expr = copy.deepcopy(expr)
    return expr.Eval(symbol, value).integer


def prod(iterable):
    return reduce(mul, iterable, 1)

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
    def __init__(self, domain_sizes:list, memory_sizes:list, memory_layout, halo=0):
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
