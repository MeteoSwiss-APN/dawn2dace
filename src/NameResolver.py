
class NameResolver:
    def __init__(self, accessIDToName:dict, exprIDToAccessID:dict, stmtIDToAccessID:dict):
        self.__accessIDToName_ = accessIDToName
    
    def FromAccessID(self, id:int) -> str:
        return self.__accessIDToName_[id]
