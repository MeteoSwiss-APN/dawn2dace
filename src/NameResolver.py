
class NameResolver:
    def __init__(self, accessIDToName:dict, exprIDToAccessID:dict, stmtIDToAccessID:dict):
        self.__accessIDToName_ = accessIDToName
        self.__exprIDToAccessID = exprIDToAccessID
        self.__stmtIDToAccessID = stmtIDToAccessID
    
    def FromAccessID(self, id:int) -> str:
        return self.__accessIDToName_[id]

    def FromExpression(self, expr) -> str:
        return self.FromAccessID(self.__exprIDToAccessID[expr.ID])

    def FromStatement(self, stmt) -> str:
        return self.FromAccessID(self.__stmtIDToAccessID[stmt.ID])
    
    def ExprToAccessID(self, expr) -> int:
        return self.__exprIDToAccessID[expr.ID]
