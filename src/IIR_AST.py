import IIR_pb2

def _qualname(obj):
    """Get the fully-qualified name of an object (including module)."""
    return obj.__module__ + '.' + obj.__qualname__

def _declaring_class(obj):
    """Get the name of the class that declared an object."""
    name = _qualname(obj)
    return name[:name.rfind('.')]

# Stores the actual visitor methods
_methods = {}

# Delegating visitor implementation
def _visitor_impl(self, arg):
    """Actual visitor method implementation."""
    key = (_qualname(type(self)), type(arg))
    if key in _methods:
        return _methods[key](self, arg)
    for base in self.__class__.__bases__:
        key = (_qualname(base), type(arg))
        if key in _methods:
            return _methods[key](self, arg)

# The actual @visitor decorator
def visitor(arg_type):
    """Decorator that creates a visitor method."""

    def decorator(fn):
        declaring_class = _declaring_class(fn)
        _methods[(declaring_class, arg_type)] = fn

        # Replace all decorated methods with _visitor_impl
        return _visitor_impl

    return decorator

def DowncastStmt(stmt):
    which = stmt.WhichOneof("stmt")
    if which == "block_stmt":
        return stmt.block_stmt
    if which == "expr_stmt":
        return stmt.expr_stmt
    if which == "var_decl_stmt":
        return stmt.var_decl_stmt
    if which == "if_stmt":
        return stmt.if_stmt
    raise ValueError("Unexpected statement: " + which)

def DowncastExpr(expr):
    which = expr.WhichOneof("expr")
    if which == "unary_operator":
        return expr.unary_operator
    if which == "binary_operator":
        return expr.binary_operator
    if which == "assignment_expr":
        return expr.assignment_expr
    if which == "ternary_operator":
        return expr.ternary_operator
    if which == "fun_call_expr":
        return expr.fun_call_expr
    if which == "var_access_expr":
        return expr.var_access_expr
    if which == "field_access_expr":
        return expr.field_access_expr
    if which == "literal_access_expr":
        return expr.literal_access_expr
    raise ValueError("Unexpected expression: " + which)

class IIR_Visitor:
    @visitor(IIR_pb2.SIR_dot_statements__pb2.Stmt)
    def visit(self, stmt):
        self.visit(DowncastStmt(stmt))

    @visitor(IIR_pb2.SIR_dot_statements__pb2.Expr)
    def visit(self, expr):
        self.visit(DowncastExpr(expr))

    @visitor(IIR_pb2.SIR_dot_statements__pb2.BlockStmt)
    def visit(self, stmt):
        for s in stmt.statements:
            self.visit(s)

    @visitor(IIR_pb2.SIR_dot_statements__pb2.ExprStmt)
    def visit(self, stmt):
        self.visit(stmt.expr)

    @visitor(IIR_pb2.SIR_dot_statements__pb2.ReturnStmt)
    def visit(self, stmt):
        self.visit(stmt.expr)

    @visitor(IIR_pb2.SIR_dot_statements__pb2.VarDeclStmt)
    def visit(self, stmt):
        for expr in stmt.init_list:
            self.visit(expr)

    @visitor(IIR_pb2.SIR_dot_statements__pb2.StencilCallDeclStmt)
    def visit(self, stmt):
        pass

    @visitor(IIR_pb2.SIR_dot_statements__pb2.VerticalRegionDeclStmt)
    def visit(self, stmt):
        pass

    @visitor(IIR_pb2.SIR_dot_statements__pb2.BoundaryConditionDeclStmt)
    def visit(self, stmt):
        pass

    @visitor(IIR_pb2.SIR_dot_statements__pb2.IfStmt)
    def visit(self, stmt):
        self.visit(stmt.cond_part)
        self.visit(stmt.then_part)
        self.visit(stmt.else_part)

    @visitor(IIR_pb2.SIR_dot_statements__pb2.UnaryOperator)
    def visit(self, stmt):
        self.visit(stmt.operand)
    
    @visitor(IIR_pb2.SIR_dot_statements__pb2.BinaryOperator)
    def visit(self, stmt):
        self.visit(stmt.left)
        self.visit(stmt.right)
    
    @visitor(IIR_pb2.SIR_dot_statements__pb2.AssignmentExpr)
    def visit(self, expr):
        self.visit(expr.left)
        self.visit(expr.right)
    
    @visitor(IIR_pb2.SIR_dot_statements__pb2.TernaryOperator)
    def visit(self, stmt):
        self.visit(stmt.cond)
        self.visit(stmt.left)
        self.visit(stmt.right)
    
    @visitor(IIR_pb2.SIR_dot_statements__pb2.FunCallExpr)
    def visit(self, expr):
        for arg in expr.arguments:
            self.visit(arg)
    
    @visitor(IIR_pb2.SIR_dot_statements__pb2.StencilFunCallExpr)
    def visit(self, expr):
        for arg in expr.arguments:
            self.visit(arg)
    
    @visitor(IIR_pb2.SIR_dot_statements__pb2.StencilFunArgExpr)
    def visit(self, expr):
        pass
    
    @visitor(IIR_pb2.SIR_dot_statements__pb2.VarAccessExpr)
    def visit(self, expr):
        pass
    
    @visitor(IIR_pb2.SIR_dot_statements__pb2.FieldAccessExpr)
    def visit(self, expr):
        pass
    
    @visitor(IIR_pb2.SIR_dot_statements__pb2.LiteralAccessExpr)
    def visit(self, expr):
        pass
    
    @visitor(IIR_pb2.SIR_dot_statements__pb2.ReductionOverNeighborExpr)
    def visit(self, expr):
        self.visit(expr.rhs)
        self.visit(expr.init)
