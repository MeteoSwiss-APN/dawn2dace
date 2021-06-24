from IdResolver import IdResolver
import IIR_pb2

def EscapePythonKeywords(word: str) -> str:
    keywords = {"False", "class", "finally", "is", "return", "None", 
        "continue", "for", "lambda", "try", "True", "def", "from", 
        "nonlocal", "while", "and", "del", "global", "not", "with", 
        "as", "elif", "if", "or", "yield", "assert", "else", "import", 
        "pass", "break", "except", "in", "raise"}
    if word in keywords:
        return word + '_'
    return word

class Unparser:
    """Unparses IIR's AST into Python."""
    def __init__(self, id_resolver:IdResolver):
        self.id_resolver = id_resolver

    def _unparse_logical_operator(self, op) -> str:
        return {'&&':'and', '||':'or', '!':'not'}.get(op, op)

    def _unparse_unary_operator(self, expr) -> str:
        return "{} ({})".format(
            self._unparse_logical_operator(expr.op),
            self._unparse_expr(expr.operand)
        )

    def _unparse_binary_operator(self, expr) -> str:
        return "({}) {} ({})".format(
            self._unparse_expr(expr.left),
            self._unparse_logical_operator(expr.op),
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
        
        if expr.callee.startswith('gridtools::dawn::math::'):
            callee = expr.callee[len('gridtools::dawn::math::'):]
        else:
            callee = expr.callee

        args = (self._unparse_expr(arg) for arg in expr.arguments)
        return callee + "(" + ",".join(args) + ")"

    def _unparse_var_access_expr(self, expr) -> str:
        name = self.id_resolver.GetName(expr.data.accessID.value)
        name = EscapePythonKeywords(name)
        return name

    def _unparse_field_access_expr(self, expr) -> str:
        id = expr.data.accessID.value
        name = self.id_resolver.GetName(id)
        name = EscapePythonKeywords(name)
        dims = self.id_resolver.GetDimensions(id)

        indices = []
        if dims.i:
            indices.append(expr.cartesian_offset.i_offset)
        if dims.j:
            indices.append(expr.cartesian_offset.j_offset)
        if dims.k:
            indices.append(expr.vertical_offset)

        if indices:
            return name + str(indices)
        return name
    
    @staticmethod
    def _unparse_literal_access_expr(expr) -> str:
        if expr.type.type_id == IIR_pb2.SIR_dot_statements__pb2.BuiltinType.Boolean:
            return "True" if expr.value else "False"
        if expr.type.type_id == IIR_pb2.SIR_dot_statements__pb2.BuiltinType.Integer:
            return expr.value
        if expr.type.type_id == IIR_pb2.SIR_dot_statements__pb2.BuiltinType.Float:
            return '{:f}'.format(float(expr.value))
        if expr.type.type_id == IIR_pb2.SIR_dot_statements__pb2.BuiltinType.Double:
            return '{:f}'.format(float(expr.value))
        if expr.type.type_id == IIR_pb2.SIR_dot_statements__pb2.BuiltinType.Invalid:
            raise ValueError(expr.type.type_id + " not supported")
        if expr.type.type_id == IIR_pb2.SIR_dot_statements__pb2.BuiltinType.Auto:
            raise ValueError(expr.type.type_id + " not supported")
        raise ValueError(expr.type.type_id + " not supported")

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
        name = self.id_resolver.GetName(var_decl.var_decl_stmt_data.accessID.value)
        
        if not var_decl.init_list:
            return name

        # single value initialization. e.g. "a = 3"
        if len(var_decl.init_list) == 1:
            return '{} {} {}'.format(name, var_decl.op, self._unparse_expr(var_decl.init_list[0]))

        # array initialization. e.g. "a = (0, 1, 2)"
        return '{} {} ({})'.format(name, var_decl.op, ', '.join(self._unparse_expr(expr) for expr in var_decl.init_list))

    def _unparse_if_stmt(self, stmt) -> str:
        if stmt.cond_part.WhichOneof("stmt") != "expr_stmt":
            raise ValueError("Not expected stmt")
        return (
            'if ({}):\n'
            '\t{}\n'
            'else:\n'
            '\t{}').format(
               self._unparse_expr_stmt(stmt.cond_part.expr_stmt), 
               self.unparse_body_stmt(stmt.then_part).replace('\n', '\n\t'),
               self.unparse_body_stmt(stmt.else_part).replace('\n', '\n\t')
            )

    def _unparse_block_stmt(self, stmt) -> str:
        return '\n'.join(self.unparse_body_stmt(s) for s in stmt.statements)

    def unparse_body_stmt(self, stmt) -> str:
        which = stmt.WhichOneof("stmt")
        if which is None:
            return 'pass'
        if which == "expr_stmt":
            return self._unparse_expr_stmt(stmt.expr_stmt)
        if which == "var_decl_stmt":
            return self._unparse_var_decl_stmt(stmt.var_decl_stmt)
        if which == "if_stmt":
            return self._unparse_if_stmt(stmt.if_stmt)
        if which == "block_stmt":
            return self._unparse_block_stmt(stmt.block_stmt)
        raise ValueError("Unexpected stmt: " + which)
