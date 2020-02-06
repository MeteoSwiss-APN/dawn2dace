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
    def __init__(self, code, reads:dict, writes:dict):
        self.id = CreateUID()
        self.code = code
        self.reads = reads # dict of MemoryAccess3D
        self.writes = writes # dict of MemoryAccess3D
    
    def __str__(self):
        return "Stmt{}".format(self.id)

    @staticmethod
    def __GetSpan(transaction):
        return MemoryAccess3D.GetSpan((x for _, x in transaction.items()))

    def GetReadSpan(self):
        return self.__GetSpan(self.reads)

    def GetWriteSpan(self):
        return self.__GetSpan(self.writes)
        

class DoMethod:
    def __init__(self, k_interval:K_Interval, statements:list):
        self.uid = CreateUID()
        self.k_interval = k_interval
        self.statements = statements # List of Statement

    def GetReadSpan(self):
        return MemoryAccess3D.GetSpan((x.GetReadSpan() for x in self.statements if x.reads))

    def GetWriteSpan(self):
        return MemoryAccess3D.GetSpan((x.GetWriteSpan() for x in self.statements if x.writes))


class Stage:
    def __init__(self, do_methods:list):
        self.uid = CreateUID()
        self.do_methods = do_methods

    def GetReadSpan(self):
        return MemoryAccess3D.GetSpan((x.GetReadSpan() for x in self.do_methods))

    def GetWriteSpan(self):
        return MemoryAccess3D.GetSpan((x.GetWriteSpan() for x in self.do_methods))


class ExecutionOrder(Enum):
    Forward_Loop = 0
    Backward_Loop = 1
    Parallel = 2


class MultiStage:
    def __init__(self, execution_order:ExecutionOrder, stages:list):
        self.uid = CreateUID()
        self.execution_order = execution_order
        self.stages = stages
        self.lower_k = None
        self.upper_k = None

    def __str__(self):
        return "state_{}".format(self.uid)

    def GetReadSpan(self):
        return MemoryAccess3D.GetSpan((x.GetReadSpan() for x in self.stages))

    def GetWriteSpan(self):
        return MemoryAccess3D.GetSpan((x.GetWriteSpan() for x in self.stages))


class Stencil:
    def __init__(self, multi_stages:list):
        if not isinstance(multi_stages, list):
            raise TypeError("Expected list, got: {}".format(type(multi_stages).__name__))
        for x in multi_stages:
            if not isinstance(x, MultiStage):
                raise TypeError("Expected MultiStage, got: {}".format(type(x).__name__))

        self.multi_stages = multi_stages # list of MultiStage
