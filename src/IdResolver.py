
class IdResolver:
    def __init__(self, accessIDToName:dict,
        APIFieldIDs:list, temporaryFieldIDs:list,
        globalVariableIDs:list, fieldIDtoLegalDimensions:list):
        self.__accessIDToName = accessIDToName
        self.__APIFieldIDs = APIFieldIDs
        self.__temporaryFieldIDs = temporaryFieldIDs
        self.__globalVariableIDs = globalVariableIDs
        self.__fieldIDtoLegalDimensions = fieldIDtoLegalDimensions
    
    def GetName(self, id:int) -> str:
        return self.__accessIDToName[id]

    def GetDimensions(self, id:int) -> list:
        """ Returns a list containing dimensional information """
        if self.IsLocal(id):
            return [1,1,1]
        array = self.__fieldIDtoLegalDimensions[id]
        return [array.int1, array.int2, array.int3]
    
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