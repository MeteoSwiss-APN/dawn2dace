from enum import Enum

def relative_number_to_str(number: int, relative: bool, literal: str) -> str:
    if not relative:
        return str(number)
    if number > 0:
        return literal + "+" + str(number)
    if number < 0:
        return literal + "-" + str(-number)
    return literal


def CreateUID() -> int:
    """ Creates unique identification numbers. """
    if not hasattr(CreateUID, "counter"):
        CreateUID.counter = 0
    CreateUID.counter += 1
    return CreateUID.counter


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


class RelMemAcc1D:
    """ A relative memory access in 1 dimension [lower, upper]. """

    def __init__(self, lower: int, upper: int):
        self.lower = lower
        self.upper = upper

    def offset(self, value: int = 0):
        self.lower += value
        self.upper += value
        return self

    @classmethod
    def BoundingBox(cls, mem_accs):
        # Make list without None
        mem_accs = [x for x in mem_accs if x]
        if len(mem_accs) == 0:
            return None
        return cls(
            min(m.lower for m in mem_accs),
            max(m.upper for m in mem_accs)
        )


class RelMemAcc3D(Any3D):
    """ A relativ memory access in 3 dimensions. """

    def __init__(self, i_lower, i_upper, j_lower, j_upper, k_lower, k_upper):
        Any3D.__init__(self,
                       RelMemAcc1D(i_lower, i_upper),
                       RelMemAcc1D(j_lower, j_upper),
                       RelMemAcc1D(k_lower, k_upper)
                       )

    def offset(self, i: int = 0, j: int = 0, k: int = 0):
        self.i.offset(i)
        self.j.offset(j)
        self.k.offset(k)
        return self

    def to_list(self) -> list:
        return [self.i.lower, self.i.upper, self.j.lower, self.j.upper, self.k.lower, self.k.upper]

    @classmethod
    def BoundingBox(cls, mem_accs):
        # Make list without None
        mem_accs = [x for x in mem_accs if x]
        if len(mem_accs) == 0:
            return None
        i = RelMemAcc1D.BoundingBox(m.i for m in mem_accs)
        j = RelMemAcc1D.BoundingBox(m.j for m in mem_accs)
        k = RelMemAcc1D.BoundingBox(m.k for m in mem_accs)
        return cls(i.lower, i.upper, j.lower, j.upper, k.lower, k.upper)


class OptionalRelMemAcc3D():
    def __init__(self, dim_present:Bool3D, mem_acc:RelMemAcc3D):
        self.dim_present = dim_present
        self.mem_acc = mem_acc
    # def __init__(self, i: bool, j: bool, k: bool, i_lower, i_upper, j_lower, j_upper, k_lower, k_upper):
    #     self.dim_present = Bool3D(i, j, k)
    #     self.mem_acc = RelMemAcc3D(i_lower, i_upper, j_lower, j_upper, k_lower, k_upper)

    def offset(self, i: int = 0, j: int = 0, k: int = 0):
        self.mem_acc.offset(i, j, k)
        return self

    @classmethod
    def Fold(cls, opt_mem_accs):
        # Make list without None
        opt_mem_accs = [x for x in opt_mem_accs if x]
        if len(opt_mem_accs) == 0:
            return None
        dim_present = Bool3D.Or(x.dim_present for x in opt_mem_accs)
        mem_acc = RelMemAcc3D.BoundingBox(x.mem_acc for x in opt_mem_accs)
        return cls(dim_present, mem_acc)


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

    def __init__(self, begin: int, end: int):
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

    def __init__(self, interval: HalfOpenInterval, begin_relative_to_K: bool, end_relative_to_K: bool):
        self.__interval = interval
        self.__begin_relative_to_K = begin_relative_to_K
        self.__end_relative_to_K = end_relative_to_K

    def begin_as_str(self, offset: int = 0) -> str:
        return relative_number_to_str(self.__interval.begin + offset, self.__begin_relative_to_K, 'K')

    def end_as_str(self, offset: int = 0) -> str:
        return relative_number_to_str(self.__interval.end + offset, self.__end_relative_to_K, 'K')

    def begin_as_value(self, K: int, offset: int = 0) -> int:
        return self.__interval.begin + offset + (K if self.__begin_relative_to_K else 0)

    def end_as_value(self, K: int, offset: int = 0) -> int:
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

    def __init__(self, lower: int, upper: int):
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

    def offset(self, value: int):
        self.lower += value
        self.upper += value
        return self


class MemoryAccess3D:
    def __init__(self, i: MemoryAccess1D, j: MemoryAccess1D, k: MemoryAccess1D):
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

    def offset(self, i: int = 0, j: int = 0, k: int = 0):
        self.i.offset(i)
        self.j.offset(j)
        self.k.offset(k)
        return self


class Statement:
    def __init__(self, code, line: int, reads: dict, writes: dict):
        self.code = code
        self.line = CreateUID()  # TODO: Replace by 'line'.
        self.reads = reads  # Dict[id, MemoryAccess3D]
        self.writes = writes  # Dict[id, MemoryAccess3D]

    def __str__(self):
        return "Line{}".format(self.line)

    def GetReadSpans(self) -> dict:  # TODO: Rename -Get.
        return self.reads

    def GetWriteSpans(self) -> dict:  # TODO: Rename -Get.
        return self.writes


class K_Section:
    def __init__(self, interval: K_Interval, statements: list = []):
        self.interval = interval
        self.statements = statements
        self.library_nodes = []

    def append(self, statement: Statement):
        self.statements.append(statement)


def FuseMemAccDicts(dicts) -> dict:
    """ dicts: An iteratable of dicts. """
    ret = {}
    for d in dicts:
        for id, mem_acc in d.items():
            if id in ret:
                ret[id] = MemoryAccess3D.GetSpan([ret[id], mem_acc])  # Hull of old an new.
            else:
                ret[id] = mem_acc
    return ret


class DoMethod:
    def __init__(self, k_interval: K_Interval, statements: list):
        self.uid = CreateUID()
        self.k_interval = k_interval
        self.statements = statements  # List of Statement

    def GetReadSpans(self) -> dict:
        return FuseMemAccDicts((x.GetReadSpans() for x in self.statements))

    def GetWriteSpans(self) -> dict:
        return FuseMemAccDicts((x.GetWriteSpans() for x in self.statements))


class Stage:
    def __init__(self, do_methods: list):
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
    def __init__(self, execution_order: ExecutionOrder, stages: list):
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


class StencilNode:
    def __init__(self, line: int, code, shape: Int3D, reads, writes, bcs):
        if not isinstance(shape, Int3D):
            raise TypeError()
        if not isinstance(reads, dict):
            raise TypeError()
        if not isinstance(writes, dict):
            raise TypeError()
        self.line = line
        self.code = code
        self.shape = shape
        self.reads = reads  # Dict[id:int, OptionalRelMemAcc3D]
        self.writes = writes  # Dict[id:int, OptionalRelMemAcc3D]
        self.state = None  # dace.state

    def offset(self, i: int = 0, j: int = 0, k: int = 0):
        self.reads = {id: x.offset(i, j, k) for id, x in self.reads}
        self.writes = {id: x.offset(i, j, k) for id, x in self.writes}
        return self

    @property
    def ReadKeys(self):
        return self.reads.keys()

    @property
    def WriteKeys(self):
        return self.writes.keys()

    def Reads(self, id: int) -> OptionalRelMemAcc3D:
        return self.reads.get(id, None)

    def Writes(self, id: int) -> OptionalRelMemAcc3D:
        return self.writes.get(id, None)

    def Transations(self, id: int) -> OptionalRelMemAcc3D:
        return OptionalRelMemAcc3D.Fold([self.Reads(id), self.Writes(id)])


class FlowControler:
    def __init__(self, interval: K_Interval, statements: list = []):
        self.interval = interval
        self.statements = statements
        self.stencil_nodes = []
        self.sdfg = None  # dace sdfg surrounding the stencil_nodes.

    def offset(self, i: int = 0, j: int = 0, k: int = 0):
        self.stencil_nodes = [x.offset(i, j, k) for x in self.stencil_nodes]
        return self

    @property
    def ReadKeys(self):
        return set().union(*(x.ReadKeys for x in self.stencil_nodes))

    @property
    def WriteKeys(self):
        return set().union(*(x.WriteKeys for x in self.stencil_nodes))

    def Reads(self, id: int) -> OptionalRelMemAcc3D:
        return OptionalRelMemAcc3D.Fold(x.Reads(id) for x in self.stencil_nodes)

    def Writes(self, id: int) -> OptionalRelMemAcc3D:
        return OptionalRelMemAcc3D.Fold(x.Writes(id) for x in self.stencil_nodes)

    def Transations(self, id: int) -> OptionalRelMemAcc3D:
        return OptionalRelMemAcc3D.Fold([self.Reads(id), self.Writes(id)])


class Map(FlowControler):
    def __init__(self, interval: K_Interval, statements: list = []):
        FlowControler.__init__(self, interval, statements)
        self.map_entry = None  # dace MapEntry
        self.map_exit = None  # dace MapExit
        self.state = None  # the surrounding dace state
        self.nested_sdfg = None

    @property
    def FirstState(self):
        return self.state

    @property
    def LastState(self):
        return self.state

class Loop(FlowControler):
    def __init__(self, interval: K_Interval, ascending: bool, statements: list = []):
        FlowControler.__init__(self, interval, statements)
        self.ascending = ascending
        self.first_state = None
        self.last_state = None

    @property
    def FirstState(self):
        return self.first_state

    @property
    def LastState(self):
        return self.last_state


class Init(FlowControler):
    def __init__(self, statements: list = []):
        FlowControler.__init__(self, None, statements)
        self.state = None  # the surrounding dace state

    @property
    def FirstState(self):
        return self.state

    @property
    def LastState(self):
        return self.state


class Stencil:
    def __init__(self, multi_stages: list):
        self.multi_stages = multi_stages  # list of MultiStage
        self.flow_controllers = []
        self.sdfg = None

    def offset(self, i: int = 0, j: int = 0, k: int = 0):
        self.flow_controllers = [x.offset(i, j, k) for x in self.flow_controllers]
        return self

    @property
    def ReadKeys(self):
        return set().union(*(x.ReadKeys for x in self.flow_controllers))

    @property
    def WriteKeys(self):
        return set().union(*(x.WriteKeys for x in self.flow_controllers))

    def Reads(self, id: int) -> OptionalRelMemAcc3D:
        return OptionalRelMemAcc3D.Fold(x.Reads(id) for x in self.flow_controllers)

    def Writes(self, id: int) -> OptionalRelMemAcc3D:
        return OptionalRelMemAcc3D.Fold(x.Writes(id) for x in self.flow_controllers)

    def Transations(self, id: int) -> OptionalRelMemAcc3D:
        return OptionalRelMemAcc3D.Fold([self.Reads(id), self.Writes(id)])
