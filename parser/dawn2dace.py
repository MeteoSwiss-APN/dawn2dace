from __future__ import print_function

import argparse
import os
import pickle
import sys

sys.path.append(
    os.path.abspath("/home/tobias/Desktop/dawn_dace/build/gen/iir_specification"))
import IIR_pb2

import dace

I = dace.symbol('I')
J = dace.symbol('J')
K = dace.symbol('K')
halo_size = dace.symbol('haloSize')

data_type = dace.float64
block_size = (32, 4)
fused = False


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


class TaskletBuilder:
    def __init__(self, _metadata):
        self.metadata_ = _metadata
        self.dataTokens_ = {}
        self.current_stmt_access_ = None
        self.state_counter_ = 0

    @staticmethod
    def visit_builtin_type(builtin_type):
        if builtin_type.type_id == 0:
            raise ValueError('Builtin type not supported')
        elif builtin_type.type_id == 1:
            return "auto"
        elif builtin_type.type_id == 2:
            return "bool"
        elif builtin_type.type_id == 3:
            return "int"
        elif builtin_type.type_id == 4:
            return "float"
        raise ValueError('Builtin type not supported')

    def visit_unary_operator(self, expr):
        return expr.op + " (" + self.visit_expr(expr.operand) + ")"

    def visit_binary_operator(self, expr):
        return "(" + self.visit_expr(expr.left) + ") " + expr.op + " (" + self.visit_expr(expr.right) + ")"

    def visit_assignment_expr(self, expr):
        return self.visit_expr(expr.left) + " " + expr.op + " (" + self.visit_expr(expr.right) + ")"

    def visit_ternary_operator(self, expr):
        return "( (" + self.visit_expr(expr.cond) + ") ? " + "(" + self.visit_expr(
            expr.left) + ") : (" + self.visit_expr(expr.right) + ") )"

    @staticmethod
    def visit_var_access_expr(expr):
        return metadata.accessIDToName[metadata.exprIDToAccessID[expr.ID]]

    def visit_field_access_expr(self, expr):
        field_id = self.metadata_.exprIDToAccessID[expr.ID]
        str_ = metadata.accessIDToName[field_id]
        # since we assume writes only to center, we only check out this map:
        access_pattern = ""
        if field_id in self.current_stmt_access_.accesses.readAccess:
            i_extent = self.current_stmt_access_.accesses.readAccess[field_id].extents[0]
            j_extent = self.current_stmt_access_.accesses.readAccess[field_id].extents[1]
            k_extent = self.current_stmt_access_.accesses.readAccess[field_id].extents[2]
            has_i = (i_extent.plus - i_extent.minus) > 0
            has_j = (j_extent.plus - j_extent.minus) > 0
            has_k = (k_extent.plus - k_extent.minus) > 0
            has_extent = has_i or has_j or has_k
            if has_extent:
                access_pattern = "["
                if has_j:
                    access_pattern += str(expr.offset[1] - j_extent.minus)
                    access_pattern += ","
                if has_k:
                    access_pattern += str(expr.offset[2] - k_extent.minus)
                    access_pattern += ","
                if has_i:
                    access_pattern += str(expr.offset[0] - i_extent.minus)
                    access_pattern += ","
                if has_extent:
                    # remove the trailing ,
                    access_pattern = access_pattern[:-1]
                    access_pattern += "]"
        return str_ + access_pattern

    @staticmethod
    def visit_literal_access_expr(expr):
        return expr.value

    # call to external function, like math::sqrt
    def visit_fun_call_expr(self, expr):
        return expr.callee + "(" + ",".join(self.visit_expr(x) for x in expr.arguments) + ")"

    def visit_expr(self, expr):
        if expr.WhichOneof("expr") == "unary_operator":
            return self.visit_unary_operator(expr.unary_operator)
        elif expr.WhichOneof("expr") == "binary_operator":
            return self.visit_binary_operator(expr.binary_operator)
        elif expr.WhichOneof("expr") == "assignment_expr":
            return self.visit_assignment_expr(expr.assignment_expr)
        elif expr.WhichOneof("expr") == "ternary_operator":
            return self.visit_ternary_operator(expr.ternary_operator)
        elif expr.WhichOneof("expr") == "fun_call_expr":
            return self.visit_fun_call_expr(expr.fun_call_expr)
        elif expr.WhichOneof("expr") == "stencil_fun_call_expr":
            raise ValueError("non supported expression")
        elif expr.WhichOneof("expr") == "stencil_fun_arg_expr":
            raise ValueError("non supported expression")
        elif expr.WhichOneof("expr") == "var_access_expr":
            return self.visit_var_access_expr(expr.var_access_expr)
        elif expr.WhichOneof("expr") == "field_access_expr":
            return self.visit_field_access_expr(expr.field_access_expr)
        elif expr.WhichOneof("expr") == "literal_access_expr":
            return self.visit_literal_access_expr(expr.literal_access_expr)
        else:
            raise ValueError("Unknown expression")

    def visit_var_decl_stmt(self, var_decl):
        # No declaration is performed
        str_ = metadata.accessIDToName[metadata.stmtIDToAccessID[var_decl.ID]]

        str_ += var_decl.op

        for expr in var_decl.init_list:
            str_ += self.visit_expr(expr)

        return str_

    def visit_expr_stmt(self, stmt):

        return self.visit_expr(stmt.expr)

    def visit_if_stmt(self, stmt):
        cond = stmt.cond_part
        if cond.WhichOneof("stmt") != "expr_stmt":
            raise ValueError("Not expected stmt")

        stmt_str = ""
        stmt_str += self.visit_body_stmt(stmt.then_part)
        stmt_str += self.visit_body_stmt(stmt.else_part)

        return stmt_str

    def visit_block_stmt(self, stmt):
        stmt_str = ""
        for each in stmt.statements:
            stmt_str += self.visit_body_stmt(each)

        return stmt_str

    def visit_body_stmt(self, stmt):
        if stmt.WhichOneof("stmt") == "var_decl_stmt":
            stmt_str = self.visit_var_decl_stmt(stmt.var_decl_stmt)
        elif stmt.WhichOneof("stmt") == "expr_stmt":
            stmt_str = self.visit_expr_stmt(stmt.expr_stmt)
        elif stmt.WhichOneof("stmt") == "if_stmt":
            stmt_str = self.visit_if_stmt(stmt.if_stmt)
        elif stmt.WhichOneof("stmt") == "block_stmt":
            stmt_str = self.visit_block_stmt(stmt.block_stmt)
        else:
            raise ValueError("Stmt not supported :" + stmt.WhichOneof("stmt"))

        return stmt_str

    @staticmethod
    def visit_interval(interval):
        str_ = ""
        if interval.WhichOneof("LowerLevel") == 'special_lower_level':
            if interval.special_lower_level == 0:
                str_ += "0"
            else:
                str_ += "K"
        elif interval.WhichOneof("LowerLevel") == 'lower_level':
            str_ += str(interval.lower_level)
        str_ += " + " + str(interval.lower_offset)
        str_ += ":"
        if interval.WhichOneof("UpperLevel") == 'special_upper_level':
            if interval.special_upper_level == 0:
                str_ += "0"
            else:
                # intervals are adapted to be inclusive so K-1 is what we want (starting from 0)
                str_ += "K-1"
        elif interval.WhichOneof("UpperLevel") == 'upper_level':
            str_ += str(interval.upper_level)
        str_ += " + " + str(interval.upper_offset)
        # since python interval are open we need to add 1
        str_ += "+1"
        return str_

    def visit_statement(self, stmt):

        return self.visit_body_stmt(stmt.ASTStmt)

    @staticmethod
    def create_extent_str(extents):
        extent_str = ""
        for extent in extents.extents:
            if not extent_str:
                extent_str = "{"
            else:
                extent_str += ","
            extent_str += str(extent.minus) + "," + str(extent.plus)

        extent_str += "}"

    def visit_access(self, accesses):
        for access_id, extents in accesses.writeAccess.iteritems():
            self.create_extent_str(extents)
        for access_id, extents in accesses.readAccess.iteritems():
            self.create_extent_str(extents)

    def visit_do_method(self, domethod):
        do_method_name = "DoMethod_" + str(domethod.doMethodID)

        do_method_name += "(" + self.visit_interval(domethod.interval) + ")"
        do_method_extent = self.visit_interval(domethod.interval)

        for stmt_access in domethod.stmtaccesspairs:
            state = sdfg.add_state('state_' + str(self.state_counter_))
            self.state_counter_ += 1

            self.current_stmt_access_ = stmt_access
            input_memlets = {}
            output_memlets = {}

            in_outs = set()

            for key in stmt_access.accesses.readAccess:
                if key in stmt_access.accesses.writeAccess:
                    in_outs.add(key)

            for key in stmt_access.accesses.readAccess:

                # since keys with negative ID's are *only* literals, we can skip those
                if key < 0:
                    continue

                f_name = self.metadata_.accessIDToName[key]

                i_extent = stmt_access.accesses.readAccess[key].extents[0]
                j_extent = stmt_access.accesses.readAccess[key].extents[1]
                k_extent = stmt_access.accesses.readAccess[key].extents[2]

                access_pattern = "j+" + str(j_extent.minus) + ":j+" + str(j_extent.plus) + "+1" + ",k+" + str(
                    k_extent.minus) + ":k+" + str(k_extent.plus) + "+1," + "i+" + str(i_extent.minus) + ":i+" + str(
                    i_extent.plus) + "+1"

                # we promote every local variable to a temporary:
                if f_name not in self.dataTokens_:
                    self.dataTokens_[f_name] = state.add_transient(f_name + "_t", shape=[J, K, I], dtype=data_type)

                if key in in_outs:
                    input_memlets[f_name + "_input"] = dace.Memlet.simple(f_name + "_t", access_pattern)
                else:
                    input_memlets[f_name] = dace.Memlet.simple(f_name + "_t", access_pattern)

            for key in stmt_access.accesses.writeAccess:

                f_name = self.metadata_.accessIDToName[key]

                i_extent = stmt_access.accesses.writeAccess[key].extents[0]
                j_extent = stmt_access.accesses.writeAccess[key].extents[1]
                k_extent = stmt_access.accesses.writeAccess[key].extents[2]

                access_pattern = "j+" + str(j_extent.minus) + ":j+" + str(j_extent.plus) + "+1" + ",k+" + str(
                    k_extent.minus) + ":k+" + str(k_extent.plus) + "+1," + "i+" + str(i_extent.minus) + ":i+" + str(
                    i_extent.plus) + "+1"

                # we promote every local variable to a temporary:
                if f_name not in self.dataTokens_:
                    self.dataTokens_[f_name] = state.add_transient(f_name + "_t", shape=[J, K, I], dtype=data_type)

                output_memlets[f_name] = dace.Memlet.simple(f_name + "_t", access_pattern)

            stmt_str = ""
            for in_out_id in in_outs:
                stmt_str += self.metadata_.accessIDToName[in_out_id] + " = " + self.metadata_.accessIDToName[
                    in_out_id] + "_input\n"

            stmt_str += self.visit_statement(stmt_access)

            if __debug__:
                print("this is the stmt-str:")
                print(stmt_str)
                print("in-mem")
                print(input_memlets)
                print("out-mem")
                print(output_memlets)

            state.add_mapped_tasklet(
                "statement",
                dict(
                    j='halo_size:J-halo_size',
                    k=do_method_extent,
                    i='halo_size:I-halo_size',
                ),
                input_memlets,
                stmt_str,
                output_memlets, external_edges=True)

    def visit_stage(self, stage):
        for do_method in stage.doMethods:
            self.visit_do_method(do_method)

    def visit_multi_stage(self, ms):
        for stage in ms.stages:
            self.visit_stage(stage)

    def visit_stencil(self, stencil_):
        for ms in stencil_.multiStages:
            self.visit_multi_stage(ms)

    @staticmethod
    def visit_fields(fields_):
        str_ = "field "
        for field in fields_:
            str_ += field.name
            dims = ["i", "j", "k"]
            dims_ = []
            for dim in range(1, 3):
                if field.field_dimensions[dim] != -1:
                    dims_.append(dims[dim])
            str_ += str(dims_)
            str_ += ","
        return str_

    def build_data_tokens(self, sdfg_):
        for fID in self.metadata_.APIFieldIDs:
            f_name = self.metadata_.accessIDToName[fID]
            array = sdfg_.add_array(f_name + "_t", shape=[J, K, I], dtype=data_type)
            self.dataTokens_[f_name] = array

        for fID in self.metadata_.temporaryFieldIDs:
            f_name = self.metadata_.accessIDToName[fID]
            self.dataTokens_[f_name] = sdfg_.add_transient(f_name + "_t", shape=[J, K, I], dtype=data_type)


if __name__ == "__main__":
    print("==== Program start ====")

    parser = argparse.ArgumentParser(
        description='''Deserializes a google protobuf file encoding an HIR example and traverses the AST printing a 
                    DSL code with the user equations''',
    )
    parser.add_argument('hirfile', type=argparse.FileType('rb'), help='google protobuf HIR file')
    parser.add_argument("I", type=int, nargs="?", default=128)
    parser.add_argument("J", type=int, nargs="?", default=128)
    parser.add_argument("K", type=int, nargs="?", default=80)

    parser.add_argument(
        "--regression", type=str2bool, nargs='?', const=True, default=True)
    args = vars(parser.parse_args())
    I.set(args["I"])
    J.set(args["J"])
    K.set(args["K"])

    print('Deserialized Example %dx%d' % (I.get(), J.get()))

    stencilInstantiation = IIR_pb2.StencilInstantiation()

    stencilInstantiation.ParseFromString(args["hirfile"].read())
    args["hirfile"].close()

    metadata = stencilInstantiation.metadata
    fields = {}
    for a in metadata.APIFieldIDs:
        fields[metadata.accessIDToName[a]] = dace.ndarray([J, K, I], dtype=data_type)

    sdfg = dace.SDFG('IIRToSDFG')

    loopFields = {}
    for a in metadata.APIFieldIDs:
        field_name = metadata.accessIDToName[a]
        sdfg.add_array('c' + field_name + "_t", shape=[J, K, I], dtype=data_type)

    des = TaskletBuilder(stencilInstantiation.metadata)

    des.build_data_tokens(sdfg)

    for stencil in stencilInstantiation.internalIR.stencils:
        des.visit_stencil(stencil)

    sdfg.fill_scope_connectors()

    nodes = list(sdfg.nodes())
    if __debug__:
        print(len(nodes))
    for i in range(len(nodes) - 1):
        sdfg.add_edge(nodes[i], nodes[i + 1],
                      dace.InterstateEdge())

    sdfg.draw_to_file('before_transformation.dot')
    sdfg.apply_strict_transformations()
    sdfg.draw_to_file('final.dot')

    pickle.dump(sdfg, open("example.sdfg", "wb"))
    sdfg.compile()
