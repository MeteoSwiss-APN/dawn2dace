import IIR_pb2

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

def iter_fields(node):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    for field in dir(node):
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass

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

IIR_Classes = (
    IIR_pb2.SIR_dot_statements__pb2.Stmt,
    IIR_pb2.SIR_dot_statements__pb2.Expr,
    IIR_pb2.SIR_dot_statements__pb2.BlockStmt,
    IIR_pb2.SIR_dot_statements__pb2.ExprStmt,
    IIR_pb2.SIR_dot_statements__pb2.ReturnStmt,
    IIR_pb2.SIR_dot_statements__pb2.VarDeclStmt,
    IIR_pb2.SIR_dot_statements__pb2.StencilCallDeclStmt,
    IIR_pb2.SIR_dot_statements__pb2.VerticalRegionDeclStmt,
    IIR_pb2.SIR_dot_statements__pb2.BoundaryConditionDeclStmt,
    IIR_pb2.SIR_dot_statements__pb2.IfStmt,
    IIR_pb2.SIR_dot_statements__pb2.UnaryOperator,
    IIR_pb2.SIR_dot_statements__pb2.BinaryOperator,
    IIR_pb2.SIR_dot_statements__pb2.AssignmentExpr,
    IIR_pb2.SIR_dot_statements__pb2.TernaryOperator,
    IIR_pb2.SIR_dot_statements__pb2.FunCallExpr,
    IIR_pb2.SIR_dot_statements__pb2.StencilFunCallExpr,
    IIR_pb2.SIR_dot_statements__pb2.StencilFunArgExpr,
    IIR_pb2.SIR_dot_statements__pb2.VarAccessExpr,
    IIR_pb2.SIR_dot_statements__pb2.FieldAccessExpr,
    IIR_pb2.SIR_dot_statements__pb2.LiteralAccessExpr,
    IIR_pb2.SIR_dot_statements__pb2.ReductionOverNeighborExpr
)

class IIR_Visitor:
    def visit(self, node):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def visit_Stmt(self, stmt):
        self.visit(DowncastStmt(stmt))

    def visit_Expr(self, expr):
        self.visit(DowncastExpr(expr))

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        for field, value in iter_fields(node):
            if field.startswith('__weakref__'):
                continue
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, IIR_Classes):
                        self.visit(item)
            elif isinstance(value, IIR_Classes):
                self.visit(value)


class IIR_Transformer(IIR_Visitor):
    def visit_Stmt(self, stmt):
        which = stmt.WhichOneof("stmt")
        if which == "block_stmt":
            stmt.block_stmt.CopyFrom(self.visit(stmt.block_stmt))
        elif which == "expr_stmt":
            stmt.expr_stmt.CopyFrom(self.visit(stmt.expr_stmt))
        elif which == "var_decl_stmt":
            stmt.var_decl_stmt.CopyFrom(self.visit(stmt.var_decl_stmt))
        elif which == "if_stmt":
            stmt.if_stmt.CopyFrom(self.visit(stmt.if_stmt))
        else:
            raise ValueError("Unexpected stmt: " + which)
        return stmt

    def visit_Expr(self, expr):
        which = expr.WhichOneof("expr")
        if which == "unary_operator":
            expr.unary_operator.CopyFrom(self.visit(expr.unary_operator))
        elif which == "binary_operator":
            expr.binary_operator.CopyFrom(self.visit(expr.binary_operator))
        elif which == "assignment_expr":
            expr.assignment_expr.CopyFrom(self.visit(expr.assignment_expr))
        elif which == "ternary_operator":
            expr.ternary_operator.CopyFrom(self.visit(expr.ternary_operator))
        elif which == "fun_call_expr":
            expr.fun_call_expr.CopyFrom(self.visit(expr.fun_call_expr))
        elif which == "var_access_expr":
            expr.var_access_expr.CopyFrom(self.visit(expr.var_access_expr))
        elif which == "field_access_expr":
            expr.field_access_expr.CopyFrom(self.visit(expr.field_access_expr))
        elif which == "literal_access_expr":
            expr.literal_access_expr.CopyFrom(self.visit(expr.literal_access_expr))
        else:
            raise ValueError("Unexpected expr: " + which)
        return expr

    def generic_visit(self, node):
        for field, old_value in iter_fields(node):
            if field.startswith('__weakref__'):
                continue
            if isinstance(old_value, list):
                new_values = []
                for value in old_value:
                    if isinstance(value, IIR_Classes):
                        value = self.visit(value)
                        if value is None:
                            continue
                        elif not isinstance(value, IIR_Classes):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, IIR_Classes):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    old_value.CopyFrom(new_node)
        return node
