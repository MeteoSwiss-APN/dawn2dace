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


class ReadOffsetterK(IIR_Transformer):
    """ Offsets the k-index by a given value per id. """
    def __init__(self, k_offsets:dict):
        self.k_offsets = k_offsets # dict[id, offset]

    def visit_AssignmentExpr(self, expr):
        """ Ignores the left side. """
        expr.right.CopyFrom(self.visit(expr.right))
        return expr

    def visit_FieldAccessExpr(self, expr):
        id = expr.data.accessID.value
        expr.vertical_offset += self.k_offsets.get(id, 0) # offsets by 0 if not in dict.
        return expr


class WriteOffsetterK(IIR_Transformer):
    """ Offsets the k-index by a given value per id. """
    def __init__(self, k_offsets:dict):
        self.k_offsets = k_offsets # dict[id, offset]

    def visit_AssignmentExpr(self, expr):
        """ Ignores the right side. """
        expr.left.CopyFrom(self.visit(expr.left))
        return expr

    def visit_FieldAccessExpr(self, expr):
        id = expr.data.accessID.value
        expr.vertical_offset += self.k_offsets.get(id, 0) # offsets by 0 if not in dict.
        return expr


class Statement:
    def __init__(self, code, line:int, reads:dict, writes:dict):
        self.code = code
        self.line = CreateUID()
        self.reads = reads # dict[id, ClosedInterval3D]
        self.writes = writes # dict[id, ClosedInterval3D]
    
    def __str__(self):
        return "Line{}".format(self.line)

    def Code(self):
        return self.code

    def Reads(self) -> dict:
        return self.reads

    def Writes(self) -> dict:
        return self.writes

    def ReadIds(self) -> set:
        return self.reads.keys()

    def WriteIds(self) -> set:
        return self.writes.keys()

    def offset_reads(self, k_offsets:dict):
        self.code = ReadOffsetterK(k_offsets).visit(self.code)
        for id, offset in k_offsets.items():
            self.reads[id].offset(k = offset)

    def offset_writes(self, k_offsets:dict):
        self.code = WriteOffsetterK(k_offsets).visit(self.code)
        for id, offset in k_offsets.items():
            self.writes[id].offset(k = offset)


class DoMethod:
    def __init__(self, k_interval:HalfOpenInterval, statements:list):
        self.uid = CreateUID()
        self.k_interval = k_interval
        self.statements = statements # List of Statement
        self.read_memlets = None
        self.write_memlets = None

    def __str__(self):
        return "DoMethod_{}".format(self.uid)

    def Code(self):
        return ''.join(stmt.code for stmt in self.statements)

    def Reads(self) -> dict:
        return FuseIntervalDicts(x.Reads() for x in self.statements)

    def Writes(self) -> dict:
        return FuseIntervalDicts(x.Writes() for x in self.statements)

    def ReadIds(self, k_interval:HalfOpenInterval=None) -> set:
        if (k_interval is None) or (self.k_interval == k_interval):
            return set().union(*[x.ReadIds() for x in self.statements])
        return set()

    def WriteIds(self, k_interval:HalfOpenInterval=None) -> set:
        if (k_interval is None) or (self.k_interval == k_interval):
            return set().union(*[x.WriteIds() for x in self.statements])
        return set()

class Stage:
    def __init__(self, do_methods:list, extents:ClosedInterval3D):
        self.uid = CreateUID()
        self.do_methods = do_methods
        self.extents = extents

    def Reads(self) -> dict:
        return FuseIntervalDicts(x.Reads() for x in self.do_methods)

    def Writes(self) -> dict:
        return FuseIntervalDicts(x.Writes() for x in self.do_methods)

    def ReadIds(self, k_interval:HalfOpenInterval=None) -> set:
        return set().union(*[x.ReadIds(k_interval) for x in self.do_methods])

    def WriteIds(self, k_interval:HalfOpenInterval=None) -> set:
        return set().union(*[x.WriteIds(k_interval) for x in self.do_methods])


class ExecutionOrder(Enum):
    Forward_Loop = 0
    Backward_Loop = 1
    Parallel = 2


class MultiStage:
    def __init__(self, execution_order:ExecutionOrder, stages:list):
        self.uid = CreateUID()
        self.execution_order = execution_order
        self.stages = stages
        self.read_memlets = None
        self.write_memlets = None

    def __str__(self):
        return "state_{}".format(self.uid)

    def Reads(self) -> dict:
        return FuseIntervalDicts(x.Reads() for x in self.stages)

    def Writes(self) -> dict:
        return FuseIntervalDicts(x.Writes() for x in self.stages)

    def ReadIds(self, k_interval:HalfOpenInterval=None) -> set:
        return set().union(*[x.ReadIds(k_interval) for x in self.stages])

    def WriteIds(self, k_interval:HalfOpenInterval=None) -> set:
        return set().union(*[x.WriteIds(k_interval) for x in self.stages])


class Stencil:
    def __init__(self, multi_stages:list):
        if not isinstance(multi_stages, list):
            raise TypeError("Expected list, got: {}".format(type(multi_stages).__name__))
        for x in multi_stages:
            if not isinstance(x, MultiStage):
                raise TypeError("Expected MultiStage, got: {}".format(type(x).__name__))

        self.multi_stages = multi_stages
