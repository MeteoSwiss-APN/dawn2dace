from IndexHandling import *
from Intermediates import Bool3D, Int3D
import dace

I = dace.symbol("I")
J = dace.symbol("J")
K = dace.symbol("K")
halo = dace.symbol("halo")

def filter_by_second(first, second) -> tuple:
    return tuple(f for f, s in zip(first, second) if s)

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
        # if self.IsLocal(id): # TODO: Think about this!
        #     return Int3D(1,1,1)
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

    def GetShape(self, id:int) -> list:
        """ Returns the shape of the array accoring to memory layout. """
        ret = filter_by_second(ToMemLayout(Any3D(I, J, K + 1)), self.GetDimensions(id)) # +1 for staggering.
        if not ret:
            return [1]
        return list(ret)

    def GetSizes(self, id:int) -> Any3D:
        dim = self.GetDimensions(id)
        return Any3D(
            I if dim.i else 0,
            J if dim.j else 0,
            K+1 if dim.k else 0 # This is a hack for the staggering in k.
        )

    def GetPaddedSize(self, id:int) -> int:
        sizes = self.GetSizes(id)
        return math.max(1, sizes[0]) * math.max(1, sizes[1]) * math.max(1, sizes[2])

    def GetStrides(self, id:int) -> list:
        """ Returns the strides according to memory layout. """
        padded_sizes = Pad(ToMemLayout(self.GetSizes(id)))

        highest = padded_sizes.i
        middle = padded_sizes.j
        lowest = padded_sizes.k

        if lowest and middle and highest:
            return [middle * lowest, lowest, 1] # 3D
        if lowest and (middle or highest):
            return [lowest, 1] # 2D and lowest is present
        if middle and highest:
            return [middle, 1] # 2D and lowest missing
        return [1] # 1D

    def GetTotalSize(self, id:int) -> int:
        highest_order_stride = self.GetStrides(id)[0]
        padded_sizes = Pad(ToMemLayout(self.GetSizes(id)))

        for x in padded_sizes:
            if x != 0:
                return x * highest_order_stride