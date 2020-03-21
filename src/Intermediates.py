from enum import Enum
from collections.abc import Iterable

def relative_number_to_str(number:int, relative:bool, literal:str) -> str:
    if not relative:
        return str(number)
    if number > 0:
        return literal + "+" + str(number)
    if number < 0:
        return literal + "-" + str(-number)
    return literal
        

class Any3D:
    def __init__(self, i, j, k):
        self.i = i
        self.j = j
        self.k = k
    def __iter__(self):
        return (x for x in [self.i, self.j, self.k])


class Int3D(Any3D):
    def __init__(self, i:int, j:int, k:int):
        Any3D.__init__(self, i, j, k)
        

class Bool3D(Any3D):
    def __init__(self, i:bool, j:bool, k:bool):
        Any3D.__init__(self, i, j, k)


class RelMemAcc1D:
    """ A relativ memory access in 1 dimension [lower, upper]. """
    def __init__(self, lower:int, upper:int):
        self.lower = lower
        self.upper = upper

class RelMemAcc3D(Any3D):
    """ A relativ memory access in 3 dimensions. """
    def __init__(self, i:RelMemAcc1D, j:RelMemAcc1D, k:RelMemAcc1D):
        Any3D.__init__(self, i, j, k)


def CreateUID() -> int:
    """ Creates unique identification numbers. """
    if not hasattr(CreateUID, "counter"):
        CreateUID.counter = 0
    CreateUID.counter += 1
    return CreateUID.counter

# class ClosedInterval:
#     """ An interval that includes its coundaries [lower, upper]. """
#     def __init__(self, lower:int, upper:int):
#         self.lower = lowers
#         self.upper = upper
#     def __str__(self) -> str:
#         return "{}:{}".format(self.lower, self.upper)
#     def __eq__(self, o) -> bool:
#         return self.lower == o.lower and self.upper == o.upper
#     def __ne__(self, o) -> bool:
#         return not self == o
#     def __hash__(self):
#         return hash(self.__dict__.values())

class HalfOpenInterval:
    """ An interval that does not includ its upper limit [begin, end). """
    def __init__(self, begin:int, end:int):
        self.begin = begin
        self.end = end
    def __str__(self) -> str:
        return "{}:{}".format(self.begin, self.end)
    def __eq__(self, o) -> bool:
        return self.begin == o.begin and self.end == o.end
    def __ne__(self, o) -> bool:
        return not self == o
    def __hash__(self):
        return hash(self.__dict__.values())


class K_Interval:
    """ Represents a half-open interval, possibly relative to K. """
    def __init__(self, interval:HalfOpenInterval, begin_relative_to_K:bool, end_relative_to_K:bool):
        self.__interval = interval
        self.__begin_relative_to_K = begin_relative_to_K
        self.__end_relative_to_K = end_relative_to_K
    
    def begin_as_str(self, offset:int = 0) -> str:
        return relative_number_to_str(self.__interval.begin + offset, self.__begin_relative_to_K, 'K')
    
    def end_as_str(self, offset:int = 0) -> str:
        return relative_number_to_str(self.__interval.end + offset, self.__end_relative_to_K, 'K')

    def begin_as_value(self, K:int, offset:int = 0) -> int:
        return self.__interval.begin + offset + (K if self.__begin_relative_to_K else 0)

    def end_as_value(self, K:int, offset:int = 0) -> int:
        return self.__interval.end + offset + (K if self.__end_relative_to_K else 0)
    
    def __str__(self) -> str:
        return "{}:{}".format(self.begin_as_str(), self.end_as_str())
    
    def __eq__(self, other) -> bool:
        return self.__interval == other.__interval \
            and self.__begin_relative_to_K == other.__begin_relative_to_K \
            and self.__end_relative_to_K == other.__end_relative_to_K
    
    def __ne__(self, other) -> bool:
        return not self == other

    def __hash__(self):
        return hash(self.__dict__.values())


class MemoryAccess1D:
    """ Represents a relativ interval [lower, upper] """

    def __init__(self, lower:int, upper:int):
        self.lower = lower
        self.upper = upper
        
    @classmethod
    def GetSpan(cls, mem_accs):
        """
        Returns the hull of intervals or None if empty.
        mem_accs: May include None. Nones are ignored.
        """

        mem_accs = [m for m in mem_accs if m is not None]
        
        if mem_accs:
            return cls(
                min((m.lower for m in mem_accs)),
                max((m.upper for m in mem_accs))
            )
        return None

    def offset(self, value:int):
        self.lower += value
        self.upper += value


class MemoryAccess3D:
    def __init__(self, i:MemoryAccess1D, j:MemoryAccess1D, k:MemoryAccess1D):
        self.i = i
        self.j = j
        self.k = k

    @classmethod
    def GetSpan(cls, mem_accs):
        """
        Returns the hull of intervals or None if empty.
        mem_accs: May include None. Nones are ignored.
        """

        mem_accs = [m for m in mem_accs if m is not None]

        if mem_accs:
            return cls(
                MemoryAccess1D.GetSpan((m.i for m in mem_accs)),
                MemoryAccess1D.GetSpan((m.j for m in mem_accs)),
                MemoryAccess1D.GetSpan((m.k for m in mem_accs))
            )
        return None

    def offset(self, i:int = 0, j:int = 0, k:int = 0):
        self.i.offset(i)
        self.j.offset(j)
        self.k.offset(k)


class Statement:
    def __init__(self, code, line:int, reads:dict, writes:dict):
        self.code = code
        self.line = CreateUID() # TODO: Replace by 'line'.
        self.reads = reads # Dict[id, MemoryAccess3D]
        self.writes = writes # Dict[id, MemoryAccess3D]
    
    def __str__(self):
        return "Line{}".format(self.line)

    def GetReadSpans(self) -> dict: # TODO: Rename -Get.
        return self.reads
    def GetWriteSpans(self) -> dict: # TODO: Rename -Get.
        return self.writes


class K_Section:
    def __init__(self, interval:K_Interval, statements:list = []):
        self.interval = interval
        self.statements = statements
        self.library_nodes = []
    
    def append(self, statement:Statement):
        self.statements.append(statement)


def FuseMemAccDicts(dicts) -> dict:
    """ dicts: An iteratable of dicts. """
    ret = {}
    for d in dicts:
        for id, mem_acc in d.items():
            if id in ret:
                ret[id] = MemoryAccess3D.GetSpan([ret[id], mem_acc]) # Hull of old an new.
            else:
                ret[id] = mem_acc
    return ret


class DoMethod:
    def __init__(self, k_interval:K_Interval, statements:list):
        self.uid = CreateUID()
        self.k_interval = k_interval
        self.statements = statements # List of Statement

    def GetReadSpans(self) -> dict:
        return FuseMemAccDicts((x.GetReadSpans() for x in self.statements))
    def GetWriteSpans(self) -> dict:
        return FuseMemAccDicts((x.GetWriteSpans() for x in self.statements))

class Stage:
    def __init__(self, do_methods:list):
        self.uid = CreateUID()
        self.do_methods = do_methods

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
        self.k_sections = []

    def __str__(self):
        return "state_{}".format(self.uid)

    def GetReadSpans(self) -> dict:
        return FuseMemAccDicts((x.GetReadSpans() for x in self.stages))
    def GetWriteSpans(self) -> dict:
        return FuseMemAccDicts((x.GetWriteSpans() for x in self.stages))


# class VariableAccess:
#     def __init__(self, id:int, in_api:bool, code_name, relative_offsets:list):
#         self.id = id
#         self.in_api = in_api
#         self.temporary = temporary #TODO: What is this guys scope? Rename!
#         # self.global = global # has global scope.
#         self.local = local # Scope within ??? #TODO replace ???.
#         self.code_name = code_name
#         self.array_name = array_name
#         self.relative_offsets = relative_offsets
        

class StencilNode:
    def __init__(self, line:int, code, shape:Int3D, reads, writes, bcs):
        self.line = line
        self.code = code
        self.shape = shape
        self.reads = reads # Dict[id:int, (dimension_present:Bool3D, RelMemAcc3D]]
        self.writes = writes # Dict[id:int, (dimension_present:Bool3D, RelMemAcc3D]]
        self.bcs = bcs # boundary conditions. Dict[id:int, RelMemAcc3D]
        self.state = None # dace.state
    @property
    def ReadKeys(self):
        return self.reads.keys()
    @property
    def WriteKeys(self):
        return self.writes.keys()


class ControlFlow:
    def __init__(self, interval:K_Interval, statements:list = []):
        self.interval = interval
        self.statements = statements
        self.stencil_nodes = []
    @property
    def ReadKeys(self):
        keys = set()
        for sn in self.stencil_nodes:
            keys.union(sn.ReadKeys)
        return keys
    @property
    def WriteKeys(self):
        keys = set()
        for sn in self.stencil_nodes:
            keys.union(sn.WriteKeys)
        return keys

class Map(ControlFlow):
    def __init__(self, interval:K_Interval, statements:list = []):
        ControlFlow.__init__(self, interval, statements)
        self.state = None # dace state
        self.sdfg = None # dace sdfg
        self.map_entry = None # dace MapEntry
        self.map_exit = None # dace MapExit
        self.nested_sdfg = None

class Loop(ControlFlow):
    def __init__(self, interval:K_Interval, ascending:bool, statements:list = []):
        ControlFlow.__init__(self, interval, statements)
        self.ascending = ascending
        self.first_state = None
        self.last_state = None


class Stencil:
    def __init__(self, multi_stages:list):
        if not isinstance(multi_stages, list):
            raise TypeError("Expected list, got: {}".format(type(multi_stages).__name__))
        for x in multi_stages:
            if not isinstance(x, MultiStage):
                raise TypeError("Expected MultiStage, got: {}".format(type(x).__name__))

        self.multi_stages = multi_stages # list of MultiStage
        self.control_flow = []
    @property
    def ReadKeys(self):
        keys = set()
        for cf in self.control_flow:
            keys.union(cf.ReadKeys)
        return keys
    @property
    def WriteKeys(self):
        keys = set()
        for cf in self.control_flow:
            keys.union(cf.WriteKeys)
        return keys

D2D_Classes = (
    Stencil,
    Loop,
    Map,
    StencilNode,
    MultiStage,
    Stage,
    DoMethod,
    K_Interval,
    K_Section,
    Statement
)

def iter_fields(node):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    for field in dir(node):
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass

class D2D_Visitor:
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        visitor(node)

    def visit_list(self, node:list):
        for n in node:
            if isinstance(n, D2D_Classes):
                self.visit(n)

    def generic_visit(self, node):
        for field, value in iter_fields(node):
            if field.startswith('_'):
                continue
            if isinstance(value, D2D_Classes):
                self.visit(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, D2D_Classes):
                        self.visit(item)


class D2D_Transformer(D2D_Visitor):
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def visit_list(self, node:list):
        new_list = []
        for n in node:
            if isinstance(n, D2D_Classes):
                novum = self.visit(n)
                if novum is not None:
                    new_list.append(novum)
        return new_list

    def generic_visit(self, node):
        for field, old_value in iter_fields(node):
            if field.startswith('_'):
                continue
            if isinstance(old_value, D2D_Classes):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    old_value = new_node
            elif isinstance(old_value, Iterable):
                for o in old_value:
                    if isinstance(o, D2D_Classes):
                        new_node = self.visit(o)
                        if new_node is None:
                            delattr(node, field)
                        else:
                            o = new_node
        return node