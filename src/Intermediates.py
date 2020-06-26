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


def MergeMemAccDicts(dicts) -> dict:
    """ dicts: An iteratable of dicts. """
    ret = {}
    for d in dicts:
        for id, mem_acc in d.items():
            if id in ret:
                ret[id] = MemoryAccess3D.GetSpan([ret[id], mem_acc])  # Hull of old an new.
            else:
                ret[id] = mem_acc
    return ret
    

class Statement:
    def __init__(self, code, line:int, reads:dict, writes:dict):
        self.code = code
        self.line = CreateUID()
        self.reads = reads # dict[id, MemoryAccess3D]
        self.writes = writes # dict[id, MemoryAccess3D]
        self.unoffsetted_read_spans = None #dict[id, mem_acc_3D]
        self.unoffsetted_write_spans = None #dict[id, mem_acc_3D]
    
    def __str__(self):
        return "Line{}".format(self.line)

    def GetReadSpans(self) -> dict:
        return self.reads
    def GetWriteSpans(self) -> dict:
        return self.writes

    def SaveSpans(self):
        import copy
        self.unoffsetted_read_spans = copy.deepcopy(self.GetReadSpans())
        self.unoffsetted_write_spans = copy.deepcopy(self.GetWriteSpans())
        

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

    def __str__(self):
        return "Line{}".format(self.uid)

    def GetReadSpans(self) -> dict:
        return FuseMemAccDicts((x.GetReadSpans() for x in self.statements))
    def GetWriteSpans(self) -> dict:
        return FuseMemAccDicts((x.GetWriteSpans() for x in self.statements))

class Stage:
    def __init__(self, do_methods:list, i_minus, i_plus, j_minus, j_plus, k_minus, k_plus):
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
        self.unoffsetted_read_spans = None #dict[id, mem_acc_3D]
        self.unoffsetted_write_spans = None #dict[id, mem_acc_3D]

    def __str__(self):
        return "state_{}".format(self.uid)

    def GetReadSpans(self) -> dict:
        return FuseMemAccDicts((x.GetReadSpans() for x in self.stages))
    def GetWriteSpans(self) -> dict:
        return FuseMemAccDicts((x.GetWriteSpans() for x in self.stages))

    def SaveSpans(self):
        import copy
        self.unoffsetted_read_spans = copy.deepcopy(self.GetReadSpans())
        self.unoffsetted_write_spans = copy.deepcopy(self.GetWriteSpans())



class Stencil:
    def __init__(self, multi_stages:list):
        if not isinstance(multi_stages, list):
            raise TypeError("Expected list, got: {}".format(type(multi_stages).__name__))
        for x in multi_stages:
            if not isinstance(x, MultiStage):
                raise TypeError("Expected MultiStage, got: {}".format(type(x).__name__))

        self.multi_stages = multi_stages # list of MultiStage
