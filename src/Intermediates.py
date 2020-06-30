from enum import Enum
from helpers import *


def CreateUID() -> int:
    """ Creates unique identification numbers. """
    if not hasattr(CreateUID, "counter"):
        CreateUID.counter = 0
    CreateUID.counter += 1
    return CreateUID.counter
 

class Statement:
    def __init__(self, code, line:int, reads:dict, writes:dict):
        self.code = code
        self.line = CreateUID()
        self.reads = reads # dict[id, RelMemAcc3D]
        self.writes = writes # dict[id, RelMemAcc3D]
        self.unoffsetted_read_spans = copy.deepcopy(self.reads) #dict[id, RelMemAcc3D]
        self.unoffsetted_write_spans = copy.deepcopy(self.writes) #dict[id, RelMemAcc3D]
    
    def __str__(self):
        return "Line{}".format(self.line)

    def GetReadSpans(self) -> dict:
        return self.reads
    def GetWriteSpans(self) -> dict:
        return self.writes
        

def FuseMemAccDicts(dicts) -> dict:
    """ dicts: An iteratable of dicts. """
    ret = {}
    for d in dicts:
        for id, mem_acc in d.items():
            if id in ret:
                ret[id] = Hull([ret[id], mem_acc]) # Hull of old an new.
            else:
                ret[id] = mem_acc
    return ret


class DoMethod:
    def __init__(self, k_interval:HalfOpenInterval, statements:list):
        self.uid = CreateUID()
        self.k_interval = k_interval
        self.statements = statements # List of Statement

    def __str__(self):
        return "Line{}".format(self.uid)

    def GetReadSpans(self) -> dict:
        return FuseMemAccDicts(x.GetReadSpans() for x in self.statements)
    def GetWriteSpans(self) -> dict:
        return FuseMemAccDicts(x.GetWriteSpans() for x in self.statements)

class Stage:
    def __init__(self, do_methods:list, i_minus, i_plus, j_minus, j_plus, k_minus, k_plus):
        assert i_minus >= 0
        assert i_plus >= 0
        assert j_minus >= 0
        assert j_plus >= 0
        assert k_minus >= 0
        assert k_plus >= 0

        self.uid = CreateUID()
        self.do_methods = do_methods
        self.i_minus = i_minus
        self.i_plus = i_plus
        self.j_minus = j_minus
        self.j_plus = j_plus
        self.k_minus = k_minus
        self.k_plus = k_plus

    def GetReadSpans(self) -> dict:
        return FuseMemAccDicts((x.GetReadSpans() for x in self.do_methods))
    def GetWriteSpans(self) -> dict:
        return FuseMemAccDicts((x.GetWriteSpans() for x in self.do_methods))


class ExecutionOrder(Enum):
    Forward_Loop = 0
    Backward_Loop = 1
    Parallel = 2


class MultiStage:
    def __init__(self, execution_order:ExecutionOrder, stages:list):
        self.uid = CreateUID()
        self.execution_order = execution_order
        self.stages = stages
        self.unoffsetted_read_spans = copy.deepcopy(self.GetReadSpans())
        self.unoffsetted_write_spans = copy.deepcopy(self.GetWriteSpans())

    def __str__(self):
        return "state_{}".format(self.uid)

    def GetReadSpans(self) -> dict:
        return FuseMemAccDicts(x.GetReadSpans() for x in self.stages)
    def GetWriteSpans(self) -> dict:
        return FuseMemAccDicts(x.GetWriteSpans() for x in self.stages)


class Stencil:
    def __init__(self, multi_stages:list):
        if not isinstance(multi_stages, list):
            raise TypeError("Expected list, got: {}".format(type(multi_stages).__name__))
        for x in multi_stages:
            if not isinstance(x, MultiStage):
                raise TypeError("Expected MultiStage, got: {}".format(type(x).__name__))

        self.multi_stages = multi_stages # list of MultiStage
