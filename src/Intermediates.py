from enum import Enum

def CreateUID() -> int:
    """ Creates unique identification numbers. """
    if not hasattr(CreateUID, "counter"):
        CreateUID.counter = 0
    CreateUID.counter += 1
    return CreateUID.counter

class K_Interval:
    """ Represents an interval [begin, end) in dimention K """

    def __init__(self, begin, end, sort_key:int):
        self.begin = begin
        self.end = end
        self.sort_key = sort_key

    def __str__(self) -> str:
        return "{}:{}".format(self.begin, self.end)

    def __eq__(self, other) -> bool:
        return self.begin == other.begin and self.end == other.end

    def __ne__(self, other) -> bool:
        return not self == other

    def __hash__(self):
        return hash(self.__dict__.values())


class MemoryAccess1D:
    """ Represents a relativ interval [begin, end] """
    # TODO: Rename lower,upper = begin,end

    def __init__(self, begin:int, end:int):
        self.begin = begin
        self.end = end

    def offset(self, value:int):
        self.begin += value
        self.end += value


class MemoryAccess3D:
    def __init__(self, i:MemoryAccess1D, j:MemoryAccess1D, k:MemoryAccess1D):
        self.i = i
        self.j = j
        self.k = k

    def offset(self, i:int = 0, j:int = 0, k:int = 0):
        self.i.offset(i)
        self.j.offset(j)
        self.k.offset(k)

class Statement:
    def __init__(self, code:str, reads:dict, writes:dict):
        self.id = CreateUID()
        self.code = code
        self.reads = reads # dict of MemoryAccess3D
        self.writes = writes # dict of MemoryAccess3D
    
    def __str__(self):
        return "Statement_{}".format(self.id)

    def GetMinReadInK(self):
        return min((read.k.begin for _, read in self.reads.items()))

    def GetMaxReadInK(self):
        return max((read.k.end for _, read in self.reads.items()))


class DoMethod:
    def __init__(self, k_interval:K_Interval, statements:list):
        self.uid = CreateUID()
        self.k_interval = k_interval
        self.statements = statements # List of Statement

    def GetMinReadInK(self):
        return min((x.GetMinReadInK() for x in self.statements))

    def GetMaxReadInK(self):
        return max((x.GetMaxReadInK() for x in self.statements))


class Stage:
    def __init__(self, do_methods:list):
        self.uid = CreateUID()
        self.do_methods = do_methods

    def GetMinReadInK(self) -> int:
        return min((x.GetMinReadInK() for x in self.do_methods))

    def GetMaxReadInK(self) -> int:
        return max((x.GetMaxReadInK() for x in self.do_methods))


class ExecutionOrder(Enum):
    Forward_Loop = 0
    Backward_Loop = 1
    Parallel = 2


class MultiStage:
    def __init__(self, execution_order:ExecutionOrder, stages:list):
        self.uid = CreateUID()
        self.execution_order = execution_order
        self.stages = stages

    def __str__(self):
        return "state_{}".format(self.uid)

    def GetMinReadInK(self) -> int:
        return min((x.GetMinReadInK() for x in self.stages))

    def GetMaxReadInK(self) -> int:
        return max((x.GetMaxReadInK() for x in self.stages))


class Stencil:
    def __init__(self, multi_stages:list):
        if not isinstance(multi_stages, list):
            raise TypeError("Expected list, got: {}".format(type(multi_stages).__name__))
        for x in multi_stages:
            if not isinstance(x, MultiStage):
                raise TypeError("Expected MultiStage, got: {}".format(type(x).__name__))

        self.multi_stages = multi_stages # list of MultiStage
