import itertools
import copy

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2,s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

class Any3D:
    def __init__(self, i, j, k):
        self.i = i
        self.j = j
        self.k = k

    def __iter__(self):
        return (x for x in [self.i, self.j, self.k])

    def __eq__(self, o) -> bool:
        return (self.i == o.i) and (self.j == o.j) and (self.k == o.k)

    def __ne__(self, o) -> bool:
        return not self == o

    def __str__(self) -> str:
        return ', '.join([str(self.i), str(self.j), str(self.k)])


class Int3D(Any3D):
    def __init__(self, i:int, j:int, k:int):
        Any3D.__init__(self, i, j, k)


class Bool3D(Any3D):
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


class SymbolicSum:
    def __init__(self, symbols:list=[], positive:list=None, integer:int=0):
        if positive is None:
            positive = [True for _ in symbols]
        self.symbols = symbols
        self.positive = positive
        self.integer = integer

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
                
        if self.IsInteger():
            return self.integer + sum
        return SymbolicSum(symbols, positive, self.integer + sum)


def Eval(expr, symbol, value):
    if isinstance(expr, int):
        return expr
    return expr.Eval(symbol, value)


class HalfOpenInterval:
    """ An interval that does not includ its upper limit [lower, upper). """

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

    def to_closed_interval(self):
        return ClosedInterval(self.lower, self.upper - 1)


class ClosedInterval:
    """ An interval that includes its coundaries [lower, upper]. """

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
        return ClosedInterval(self.lower + o, self.upper + o)

    def __sub__(self, o):
        return ClosedInterval(self.lower - o, self.upper - o)

    def __hash__(self):
        return hash(self.__dict__.values())

    def to_halfopen_interval(self):
        return HalfOpenInterval(self.lower, self.upper + 1)