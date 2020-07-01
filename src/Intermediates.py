from enum import Enum
from helpers import *
from IIR_AST import IIR_Transformer


def CreateUID() -> int:
    """ Creates unique identification numbers. """
    if not hasattr(CreateUID, "counter"):
        CreateUID.counter = 0
    CreateUID.counter += 1
    return CreateUID.counter
 

def FuseIntervalDicts(dicts) -> dict:
    """ dicts: An iteratable of dicts. """
    ret = {}
    for d in dicts:
        for id, interval in d.items():
            if id in ret:
                ret[id] = Hull([ret[id], interval])
            else:
                ret[id] = interval
    return ret


class K_Offsetter(IIR_Transformer):
    """ Offsets the k-index by a given value per id. """
    def __init__(self, k_offsets:dict):
        self.k_offsets = k_offsets # dict[id, offset]

    def visit_FieldAccessExpr(self, expr):
        id = expr.data.accessID.value
        expr.vertical_offset += self.k_offsets.get(id, 0) # offsets by 0 if not in dict.
        return expr


class Statement:
    def __init__(self, code, line:int, reads:dict, writes:dict):
        self.code = code
        self.line = CreateUID()
        self.code_reads = reads # dict[id, ClosedInterval3D]
        self.code_writes = writes # dict[id, ClosedInterval3D]
        self.__original_reads = reads #dict[id, ClosedInterval3D]
        self.__original_writes = writes #dict[id, ClosedInterval3D]
    
    def __str__(self):
        return "Line{}".format(self.line)

    def CodeReads(self) -> dict:
        return self.code_reads
    def CodeWrites(self) -> dict:
        return self.code_writes
    def OriginalReads(self) -> dict:
        return self.__original_reads
    def OriginalWrites(self) -> dict:
        return self.__original_writes
    def ReadKeys(self) -> set:
        return self.code_reads.keys()
    def WriteKeys(self) -> set:
        return self.code_writes.keys()

    def offset_reads(self, k_offsets:dict):
        self.code = K_Offsetter(k_offsets).visit(self.code)
        for id, offset in k_offsets.items():
            self.code_reads[id].offset(k = offset)

    def offset_writes(self, k_offsets:dict):
        self.code = K_Offsetter(k_offsets).visit(self.code)
        for id, offset in k_offsets.items():
            self.code_writes[id].offset(k = offset)


class DoMethod:
    def __init__(self, k_interval:HalfOpenInterval, statements:list):
        self.uid = CreateUID()
        self.k_interval = k_interval
        self.statements = statements # List of Statement

    def __str__(self):
        return "Line{}".format(self.uid)

    def CodeReads(self) -> dict:
        return FuseIntervalDicts(x.CodeReads() for x in self.statements)
    def CodeWrites(self) -> dict:
        return FuseIntervalDicts(x.CodeWrites() for x in self.statements)
    def OriginalReads(self) -> dict:
        return FuseIntervalDicts(x.OriginalReads() for x in self.statements)
    def OriginalWrites(self) -> dict:
        return FuseIntervalDicts(x.OriginalWrites() for x in self.statements)
    def ReadKeys(self) -> set:
        return set().union(*[x.ReadKeys() for x in self.statements])
    def WriteKeys(self) -> set:
        return set().union(*[x.WriteKeys() for x in self.statements])

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

    def CodeReads(self) -> dict:
        return FuseIntervalDicts(x.CodeReads() for x in self.do_methods)
    def CodeWrites(self) -> dict:
        return FuseIntervalDicts(x.CodeWrites() for x in self.do_methods)
    def OriginalReads(self) -> dict:
        return FuseIntervalDicts(x.OriginalReads() for x in self.do_methods)
    def OriginalWrites(self) -> dict:
        return FuseIntervalDicts(x.OriginalWrites() for x in self.do_methods)
    def ReadKeys(self) -> set:
        return set().union(*[x.ReadKeys() for x in self.do_methods])
    def WriteKeys(self) -> set:
        return set().union(*[x.WriteKeys() for x in self.do_methods])


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

    def CodeReads(self) -> dict:
        return FuseIntervalDicts(x.CodeReads() for x in self.stages)
    def CodeWrites(self) -> dict:
        return FuseIntervalDicts(x.CodeWrites() for x in self.stages)
    def OriginalReads(self) -> dict:
        return FuseIntervalDicts(x.OriginalReads() for x in self.stages)
    def OriginalWrites(self) -> dict:
        return FuseIntervalDicts(x.OriginalWrites() for x in self.stages)
    def ReadKeys(self) -> set:
        return set().union(*[x.ReadKeys() for x in self.stages])
    def WriteKeys(self) -> set:
        return set().union(*[x.WriteKeys() for x in self.stages])


class Stencil:
    def __init__(self, multi_stages:list):
        if not isinstance(multi_stages, list):
            raise TypeError("Expected list, got: {}".format(type(multi_stages).__name__))
        for x in multi_stages:
            if not isinstance(x, MultiStage):
                raise TypeError("Expected MultiStage, got: {}".format(type(x).__name__))

        self.multi_stages = multi_stages
