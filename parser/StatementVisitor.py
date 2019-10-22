from NameResolver import NameResolver

class StatementVisitor:
    def __init__(self, name_resolver:NameResolver, access):
        self.get_name = name_resolver
        self.access = access

    def visit_unary_operator(self, expr) -> str:
        return "{} ({})".format(
            expr.op,
            self.visit_expr(expr.operand)
        )

    def visit_binary_operator(self, expr) -> str:
        return "({}) {} ({})".format(
            self.visit_expr(expr.left),
            expr.op,
            self.visit_expr(expr.right)
        )

    def visit_assignment_expr(self, expr) -> str:
        return "{} {} ({})".format(
            self.visit_expr(expr.left),
            expr.op,
            self.visit_expr(expr.right)
        )

    def visit_ternary_operator(self, expr) -> str:
        return "( ({}) ? ({}) : ({}) )".format(
            self.visit_expr(expr.cond),
            self.visit_expr(expr.left),
            self.visit_expr(expr.right)
        )

    # calls to external function, like math::sqrt.
    def visit_fun_call_expr(self, expr) -> str:
        func = expr.fun_call_expr
        args = (self.visit_expr(arg) for arg in func.arguments)
        return func.callee + "(" + ",".join(args) + ")"

    def visit_var_access_expr(self, expr) -> str:
        return self.get_name.FromExpression(expr)

    def visit_field_access_expr(self, expr) -> str:
        # since we assume writes only to center, we only check out readAccess.
        field_id = self.get_name.ExprToAccessID(expr)
        access_pattern = ""
        if field_id in self.access.readAccess:
            i,j,k = self.access.readAccess[field_id].extents
            has_i = (i.plus > i.minus)
            has_j = (j.plus > j.minus)
            has_k = (k.plus > k.minus)
            has_extent = has_i or has_j or has_k
            if has_extent:
                access_pattern = "["
                if has_j:
                    access_pattern += str(expr.offset[1] - j.minus) + ","
                if has_k:
                    access_pattern += str(expr.offset[2] - k.minus) + ","
                if has_i:
                    access_pattern += str(expr.offset[0] - i.minus) + ","                    
                # removes the trailing ','
                access_pattern = access_pattern[:-1]
                access_pattern += "]"
        return self.get_name.FromExpression(expr) + access_pattern
    
    @staticmethod
    def visit_literal_access_expr(expr) -> str:
        return expr.value

    def visit_expr(self, expr) -> str:
        which = expr.WhichOneof("expr")
        if which == "unary_operator":
            return self.visit_unary_operator(expr.unary_operator)
        if which == "binary_operator":
            return self.visit_binary_operator(expr.binary_operator)
        if which == "assignment_expr":
            return self.visit_assignment_expr(expr.assignment_expr)
        if which == "ternary_operator":
            return self.visit_ternary_operator(expr.ternary_operator)
        if which == "fun_call_expr":
            return self.visit_fun_call_expr(expr.fun_call_expr)
        if which == "var_access_expr":
            return self.visit_var_access_expr(expr.var_access_expr)
        if which == "field_access_expr":
            return self.visit_field_access_expr(expr.field_access_expr)
        if which == "literal_access_expr":
            return self.visit_literal_access_expr(expr.literal_access_expr)
        if which == "stencil_fun_call_expr":
            raise ValueError(which + " not supported")
        if which == "stencil_fun_arg_expr":
            raise ValueError(which + " not supported")
        raise ValueError("Unexpected expr: " + which)

    def visit_expr_stmt(self, stmt) -> str:
        return self.visit_expr(stmt.expr)

    def visit_var_decl_stmt(self, var_decl) -> str:
        if not var_decl.init_list:
            return ''

        ret = self.get_name.FromStatement(var_decl)
        ret += var_decl.op

        for expr in var_decl.init_list:
            ret += self.visit_expr(expr)

        return ret

    def visit_if_stmt(self, stmt) -> str:
        if stmt.cond_part.WhichOneof("stmt") != "expr_stmt":
            raise ValueError("Not expected stmt")

        ret = "if "
        ret += "True"  # TODO: Replace with 'self.visit_expr_stmt(stmt.cond_part)'.
        ret += ":\n\t"
        ret += self.visit_body_stmt(stmt.then_part)
        ret += "\nelse:\n\t"
        ret += self.visit_body_stmt(stmt.else_part)
        return ret

    def visit_block_stmt(self, stmt) -> str:
        return ''.join(self.visit_body_stmt(s) for s in stmt.statements)

    def visit_body_stmt(self, stmt) -> str:
        which = stmt.WhichOneof("stmt")
        if which == "expr_stmt":
            return self.visit_expr_stmt(stmt.expr_stmt)
        if which == "var_decl_stmt":
            return self.visit_var_decl_stmt(stmt.var_decl_stmt)
        if which == "if_stmt":
            return self.visit_if_stmt(stmt.if_stmt)
        if which == "block_stmt":
            return self.visit_block_stmt(stmt.block_stmt)
        raise ValueError("Unexpected stmt: " + which)
