from IdResolver import IdResolver
import IIR_pb2

def DownCastStatement(stmt):
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

def DownCastExpression(expr):
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


class Unparser:
    """Unparses IIR's AST into Python."""

    def _unparse_unary_operator(self, expr) -> str:
        return "{} ({})".format(
            expr.op,
            self._unparse_expr(expr.operand)
        )

    def _unparse_binary_operator(self, expr) -> str:
        return "({}) {} ({})".format(
            self._unparse_expr(expr.left),
            expr.op,
            self._unparse_expr(expr.right)
        )

    def _unparse_assignment_expr(self, expr) -> str:
        return "{} {} ({})".format(
            self._unparse_expr(expr.left),
            expr.op,
            self._unparse_expr(expr.right)
        )

    def _unparse_ternary_operator(self, expr) -> str:
        return "( ({}) if ({}) else ({}) )".format(
            self._unparse_expr(expr.left),
            self._unparse_expr(expr.cond),
            self._unparse_expr(expr.right)
        )

    def _unparse_fun_call_expr(self, expr) -> str:
        """Unparses external function calls, like math::sqrt."""
        
        func = expr.fun_call_expr
        args = (self._unparse_expr(arg) for arg in func.arguments)
        return func.callee + "(" + ",".join(args) + ")"

    def _unparse_var_access_expr(self, expr) -> str:
        return expr.name

    def _unparse_field_access_expr(self, expr) -> str:
        indices = [
            expr.cartesian_offset.j_offset,
            expr.vertical_offset,
            expr.cartesian_offset.i_offset,
        ]
        indices = [str(i) for i in indices if i != -1000]

        if indices:
            return expr.name + "[{}]".format(','.join(indices))
        return expr.name
    
    @staticmethod
    def _unparse_literal_access_expr(expr) -> str:
        return expr.value

    def _unparse_expr(self, expr) -> str:
        which = expr.WhichOneof("expr")
        if which == "unary_operator":
            return self._unparse_unary_operator(expr.unary_operator)
        if which == "binary_operator":
            return self._unparse_binary_operator(expr.binary_operator)
        if which == "assignment_expr":
            return self._unparse_assignment_expr(expr.assignment_expr)
        if which == "ternary_operator":
            return self._unparse_ternary_operator(expr.ternary_operator)
        if which == "fun_call_expr":
            return self._unparse_fun_call_expr(expr.fun_call_expr)
        if which == "var_access_expr":
            return self._unparse_var_access_expr(expr.var_access_expr)
        if which == "field_access_expr":
            return self._unparse_field_access_expr(expr.field_access_expr)
        if which == "literal_access_expr":
            return self._unparse_literal_access_expr(expr.literal_access_expr)
        if which == "stencil_fun_call_expr":
            raise ValueError(which + " not supported")
        if which == "stencil_fun_arg_expr":
            raise ValueError(which + " not supported")
        raise ValueError("Unexpected expr: " + which)

    def _unparse_expr_stmt(self, stmt) -> str:
        return self._unparse_expr(stmt.expr)

    def _unparse_var_decl_stmt(self, var_decl) -> str:
        if not var_decl.init_list:
            return ''

        ret = var_decl.name + var_decl.op

        for expr in var_decl.init_list:
            ret += self._unparse_expr(expr)

        return ret

    def _unparse_if_stmt(self, stmt) -> str:
        if stmt.cond_part.WhichOneof("stmt") != "expr_stmt":
            raise ValueError("Not expected stmt")
        
        return (
            'if ({}):\n'
            '\t{}\n'
            'else:\n'
            '\t{}').format(
               self._unparse_expr_stmt(stmt.cond_part), 
               self._unparse_body_stmt(stmt.then_part),
               self._unparse_body_stmt(stmt.else_part)
            )

    def _unparse_block_stmt(self, stmt) -> str:
        return '\n'.join(self._unparse_body_stmt(s) for s in stmt.statements)

    def unparse_body_stmt(self, stmt) -> str:
        which = stmt.WhichOneof("stmt")
        if which == "expr_stmt":
            return self._unparse_expr_stmt(stmt.expr_stmt)
        if which == "var_decl_stmt":
            return self._unparse_var_decl_stmt(stmt.var_decl_stmt)
        if which == "if_stmt":
            return self._unparse_if_stmt(stmt.if_stmt)
        if which == "block_stmt":
            return self._unparse_block_stmt(stmt.block_stmt)
        raise ValueError("Unexpected stmt: " + which)
