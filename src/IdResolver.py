from IndexHandling import *
from Intermediates import Bool3D, Int3D
import dace

I = dace.symbol("I")
J = dace.symbol("J")
K = dace.symbol("K")
halo = dace.symbol("halo")
data_type = dace.float64

def filter_by_second(first, second) -> tuple:
    return tuple(f for f, s in zip(first, second) if s)

def Replace0with1(o:Any3D) -> Any3D:
    if o.i == 0:
        o.i = 1
    if o.j == 0:
        o.j = 1
    if o.k == 0:
        o.k = 1
    return o

class IdResolver:
    def __init__(self, accessIDToName:dict,
        APIFieldIDs:list, temporaryFieldIDs:list,
        globalVariableIDs:list, fieldIDtoDimensions:list):
        self.__accessIDToName = accessIDToName
        self.__APIFieldIDs = APIFieldIDs
        self.__temporaryFieldIDs = temporaryFieldIDs
        self.__globalVariableIDs = globalVariableIDs
        self.__fieldIDtoDimensions = fieldIDtoDimensions
    
    def GetName(self, id:int) -> str:
        return self.__accessIDToName[id]

    def GetDimensions(self, id:int) -> Bool3D:
        if self.IsLocal(id): # TODO: Think about this!
            return Int3D(1,1,0)
        dims = self.__fieldIDtoDimensions[id]
        return Bool3D(
            dims.cartesian_horizontal_dimension.mask_cart_i != 0,
            dims.cartesian_horizontal_dimension.mask_cart_j != 0,
            dims.mask_k != 0
            )
    
    def IsInAPI(self, id:int) -> bool:
        return id in self.__APIFieldIDs

    def IsATemporary(self, id:int) -> bool:
        return id in self.__temporaryFieldIDs

    def IsGlobal(self, id:int) -> bool:
        return id in self.__globalVariableIDs

    def IsALiteral(self, id:int) -> bool:
        return id < 0

    def IsLocal(self, id:int) -> bool:
        return self.GetName(id).startswith("__local")

    def Classify(self, ids: list):
        """ Returns a tuple of lists of ids: (apis, temporaries, globals, literals, locals). """
        apis = {id for id in ids if self.IsInAPI(id)}
        temporaries = {id for id in ids if self.IsATemporary(id)}
        globals = {id for id in ids if self.IsGlobal(id)}
        literals = {id for id in ids if self.IsALiteral(id)}
        locals = {id for id in ids if self.IsLocal(id)}
        return apis, temporaries, globals, literals, locals

    def GetSizes(self, id:int) -> Any3D:
        dim = self.GetDimensions(id)
        return Any3D(
            I if dim.i else 0,
            J if dim.j else 0,
            K+1 if dim.k else 0 # This is a hack for the staggering in k.
        )
    
    def GetPaddedSizes(self, id:int) -> Any3D:
        return Pad(self.GetSizes(id))

    def GetTotalSize(self, id:int) -> int:
        sizes = self.GetSizes(id)
        sizes = Replace0with1(sizes)
        return sizes.i * sizes.j * sizes.k

    def GetTotalPaddedSize(self, id:int) -> int:
        sizes = self.GetPaddedSizes(id)
        sizes = Replace0with1(sizes)
        return sizes.i * sizes.j * sizes.k

    def GetStrides(self, id:int) -> Any3D:
        sizes = self.GetPaddedSizes(id)
        sizes = Replace0with1(sizes)
        return Any3D(sizes.j * sizes.k, sizes.k, 1)