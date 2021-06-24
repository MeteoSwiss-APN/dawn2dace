import ast
import astunparse
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
        if d is not None:
            for id, interval in d.items():
                if id in ret:
                    ret[id] = Hull([ret[id], interval])
                else:
                    ret[id] = interval
    return ret

def Subtract(a:dict, b:dict) -> dict:
    " returns a \ b "
    # dict[id, ClosedInterval3D]
    ret = {}
    for id, interval in a.items():
        if id == 3307:
            id = 3307
        if id in b:
            if interval == b[id]:
                continue # without adding
            else:
                ret[id] = interval
                print(ret[id], " - ", b[id], " = ")
                ret[id].exclude(b[id])
                print(ret[id])
        else:
            ret[id] = interval
    return ret


class Offsetter(ast.NodeTransformer):
    def __init__(self, offsets:dict):
        self.offsets = offsets # dict[name, tuple(offset)]

    def visit_Subscript(self, node: ast.Subscript):
        name = node.value.id
        if name not in self.offsets:
            return node
        if isinstance(node.slice.value, ast.Constant):
            return node
        for elt, offset in zip(node.slice.value.elts, self.offsets[name]):
            if isinstance(elt, ast.UnaryOp):
                elt.operand.value -= offset
            else:
                elt.value += offset
        return node


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

    def OffsetReads(self, k_offsets:dict, id_resolver):
        "k_offsets: Dict[id, offset:int]"
        if not self.writes:
            named_offsets = {}
            for id, offset_k in k_offsets.items():
                name = id_resolver.GetName(id) + '_in'
                dims = id_resolver.GetDimensions(id)
                offset = []
                if dims.i:
                    offset.append(0)
                if dims.j:
                    offset.append(0)
                if dims.k:
                    offset.append(offset_k)
                named_offsets[name] = tuple(offset)
            tree = ast.parse(self.code)
            self.code = astunparse.unparse(Offsetter(named_offsets).visit(tree))

            for id, offset in k_offsets.items():
                self.reads[id].offset(k = offset)

    def OffsetWrites(self, k_offsets:dict, id_resolver):
        "k_offsets: Dict[id, offset:int]"
        if not self.reads:
            named_offsets = {}
            for id, offset_k in k_offsets.items():
                name = id_resolver.GetName(id) + '_in'
                dims = id_resolver.GetDimensions(id)
                offset = []
                if dims.i:
                    offset.append(0)
                if dims.j:
                    offset.append(0)
                if dims.k:
                    offset.append(offset_k)
                named_offsets[name] = tuple(offset)
            tree = ast.parse(self.code)
            self.code = astunparse.unparse(Offsetter(named_offsets).visit(tree))

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
        return '\n'.join(stmt.code for stmt in self.statements)

    def Reads(self) -> dict:
        # writes = {}
        # reads = {}
        # for stmt in self.statements:
        #     reads = FuseIntervalDicts([reads, Subtract(stmt.Reads(), writes)])
        #     writes = FuseIntervalDicts([writes, stmt.Writes()])
        # return reads

        # reads = [stmt.Reads() for stmt in self.statements]
        # writes = [stmt.Writes() for stmt in self.statements]
        # accumulated_writes = []
        # acc = {}
        # for w in writes:
        #     acc = FuseIntervalDicts([acc, w])
        #     accumulated_writes.append(acc)

        # accumulated_reads = {}
        # accumulated_writes = {}
        # for stmt in self.statements:
        #     reads = Subtract(stmt.Reads(), accumulated_writes)
        #     accumulated_writes = FuseIntervalDicts([accumulated_writes, stmt.Writes()])

        # ret = {}
        # writes = {}
        # for stmt in self.statements:
        #     for id, interval in stmt.Reads().items():
        #         if id in ret:
        #             ret[id] = Hull([ret[id], interval])
        #         else:
        #             ret[id] = interval
        #     writes = FuseIntervalDicts([writes, stmt.Writes()])
        # return ret
        return FuseIntervalDicts(x.Reads() for x in self.statements)

    def Writes(self) -> dict:
        return FuseIntervalDicts(x.Writes() for x in self.statements)

    def ReadIds(self, k_interval:HalfOpenInterval = None) -> set:
        if (k_interval is None) or (self.k_interval == k_interval):
            return set().union(*[x.ReadIds() for x in self.statements])
        return set()

    def WriteIds(self, k_interval:HalfOpenInterval = None) -> set:
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
