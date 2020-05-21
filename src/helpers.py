import itertools

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2,s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def relative_number_to_str(number:int, literal:str) -> str:
    if number > 0:
        return literal + "+" + str(number)
    if number < 0:
        return literal + str(number)
    return literal


class Any3D:
    def __init__(self, i, j, k):
        self.i = i
        self.j = j
        self.k = k

    def __iter__(self):
        return (x for x in [self.i, self.j, self.k])

    def __eq__(self, o) -> bool:
        return self.i == o.i and self.j == o.j and self.k == o.k

    def __ne__(self, o) -> bool:
        return not self == o

    def __str__(self) -> str:
        return ', '.join([str(self.i), str(self.j), str(self.k)])


class Int3D(Any3D):
    def __init__(self, i: int, j: int, k: int):
        Any3D.__init__(self, i, j, k)


class Bool3D(Any3D):
    def __init__(self, i: bool, j: bool, k: bool):
        Any3D.__init__(self, i, j, k)

    @classmethod
    def Or(cls, bools) -> bool:
        # Make list without None
        bools = [x for x in bools if x]
        if len(bools) == 0:
            return None
        ret = Bool3D(False, False, False)
        for x in bools:
            ret.i |= x.i
            ret.j |= x.j
            ret.k |= x.k
        return ret


class RelativeNumber:
    def __init__(self, literal:str, number):
        self.literal = literal
        self.number = number

    def __str__(self) -> str:
        if self.number > 0:
            return self.literal + "+" + str(self.number)
        if self.number < 0:
            return self.literal + str(self.number)
        return self.literal

    def __add__(self, number):
        return RelativeNumber(self.literal, self.number + number)

    def __sub__(self, number):
        return RelativeNumber(self.literal, self.number - number)


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

    def __hash__(self):
        return hash(self.__dict__.values())