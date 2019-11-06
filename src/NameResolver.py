
class NameResolver:
    def __init__(self, accessIDToName:dict):
        self.__accessIDToName = accessIDToName
    
    def FromAccessID(self, id:int) -> str:
        return self.__accessIDToName[id]
