from IndexHandling import *

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
        """ Returns if the dimensions (i,j,k) are present in this field. """
        if self.IsLocal(id):
            return Bool3D(True, True, False)
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
