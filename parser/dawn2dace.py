from __future__ import print_function


import dace
import argparse
import ast
import os
import pickle
import sys
import astunparse

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "build", "gen", "iir_specification"))
)

import IIR_pb2


I = dace.symbol("I")
J = dace.symbol("J")
K = dace.symbol("K")
halo_size = dace.symbol("haloSize")

data_type = dace.float64
block_size = (32, 4)
fused = False


def str2bool(v):
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


class RenameInput(ast.NodeTransformer):
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            node.id += "_input"
            return node
        return node


class TaskletBuilder:
    def __init__(self, _metadata):
        self.metadata_ = _metadata
        self.dataTokens_ = {}
        self.current_stmt_access_ = None
        self.state_counter_ = 0
        self.last_state_ = None

    def fill_globals(self):
        for fID in self.metadata_.globalVariableIDs:
            f_name = self.metadata_.accessIDToName[fID]
            self.dataTokens_[f_name] = sdfg.add_scalar(f_name + "_t", dace.float32)

    @staticmethod
    def visit_builtin_type(builtin_type):
        if builtin_type.type_id == 0:
            raise ValueError("Builtin type not supported")
        elif builtin_type.type_id == 1:
            return "auto"
        elif builtin_type.type_id == 2:
            return "bool"
        elif builtin_type.type_id == 3:
            return "int"
        elif builtin_type.type_id == 4:
            return "float"
        raise ValueError("Builtin type not supported")

    def visit_unary_operator(self, expr):
        return expr.op + " (" + self.visit_expr(expr.operand) + ")"

    def visit_binary_operator(self, expr):
        return "(" + self.visit_expr(expr.left) + ") " + expr.op + " (" + self.visit_expr(expr.right) + ")"

    def visit_assignment_expr(self, expr):
        return self.visit_expr(expr.left) + " " + expr.op + " (" + self.visit_expr(expr.right) + ")"

    def visit_ternary_operator(self, expr):
        return (
            "( ("
            + self.visit_expr(expr.cond)
            + ") ? "
            + "("
            + self.visit_expr(expr.left)
            + ") : ("
            + self.visit_expr(expr.right)
            + ") )"
        )

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
        if var_decl.init_list:
            str_ = metadata.accessIDToName[metadata.stmtIDToAccessID[var_decl.ID]]

            str_ += var_decl.op

            for expr in var_decl.init_list:
                str_ += self.visit_expr(expr)

            return str_
        else:
            return ""

    def visit_expr_stmt(self, stmt):

        return self.visit_expr(stmt.expr)

    def visit_if_stmt(self, stmt):
        cond = stmt.cond_part
        if cond.WhichOneof("stmt") != "expr_stmt":
            raise ValueError("Not expected stmt")

        stmt_str = "if "
        stmt_str += "True"  # self.visit_expr_stmt(stmt.cond_part)
        stmt_str += ":\n\t"
        stmt_str += self.visit_body_stmt(stmt.then_part)
        stmt_str += "\nelse:\n\t"
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
        if interval.WhichOneof("LowerLevel") == "special_lower_level":
            if interval.special_lower_level == 0:
                start = "0"
                startint = 0
            else:
                start = "K-1"
                startint = 10000 - 1
        elif interval.WhichOneof("LowerLevel") == "lower_level":
            start = str(interval.lower_level)
            startint = interval.lower_level
        start += " + " + str(interval.lower_offset)
        startint += interval.lower_offset

        if interval.WhichOneof("UpperLevel") == "special_upper_level":
            if interval.special_upper_level == 0:
                end = "0"
                endint = 0
            else:
                # intervals are adapted to be inclusive so K-1 is what we want (starting from 0)
                end = "K-1"
                endint = 10000 - 1
        elif interval.WhichOneof("UpperLevel") == "upper_level":
            end = str(interval.upper_level)
            endint = interval.upper_level
        end += " + " + str(interval.upper_offset)
        endint += interval.upper_offset
        # since python interval are open we need to add 1
        end += "+1"
        endint += 1
        return start, end, startint

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
        extent_start, extent_end, _ = self.visit_interval(domethod.interval)
        do_method_name += "(%s:%s)" % (extent_start, extent_end)

    def visit_stage(self, stage):
        for do_method in stage.doMethods:
            self.visit_do_method(do_method)

    def visit_multi_stage(self, ms):
        intervals = set()
        for stage in ms.stages:
            for do_method in stage.doMethods:
                extent_start, extent_end, startint = self.visit_interval(do_method.interval)
                intervals.add((extent_start, extent_end, startint))
        intervals = list(intervals)
        # sort the intervals
        if ms.loopOrder == 1:
            intervals.sort(key=lambda tup: tup[2], reverse=True)
        else:
            intervals.sort(key=lambda tup: tup[2])

        if __debug__:
            print("list of all the intervals:")
            for (x, y, _) in intervals:
                print("[ " + x + " , " + y + " ]")
        # generate the multistage for every interval (in loop order)
        for interval in intervals:
            self.last_state_ = self.generate_multistage(ms.loopOrder, ms, interval)

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
            array = sdfg_.add_array(f_name + "_t", shape=[J, K + 1, I], dtype=data_type)
            self.dataTokens_[f_name] = array

        for fID in self.metadata_.temporaryFieldIDs:
            f_name = self.metadata_.accessIDToName[fID]
            self.dataTokens_[f_name] = sdfg_.add_transient(f_name + "_t", shape=[J, K + 1, I], dtype=data_type)
            print("we're here 2:%s" % f_name)

    def generate_multistage(self, loop_order, multi_stage, interval):
        if loop_order == 2:
            return self.generate_parallel(multi_stage, interval)
            #
            #
            # change this back to parallel once tal figured out the problem with the generated sdfg
            #
            #
            #
            #
            # return self.generate_loop(multi_stage, interval, 0)
        else:
            return self.generate_loop(multi_stage, interval, loop_order)

    def generate_parallel(self, multi_stage, interval):
        multi_stage_state = sdfg.add_state("state_" + str(self.state_counter_))
        self.state_counter_ += 1
        sub_sdfg = dace.SDFG("ms_subsdfg" + str(self.state_counter_))
        sub_sdfg_arrays = {}
        self.state_counter_ += 1
        last_state_in_multi_stage = None
        last_state = None
        # to connect them we need all input and output names
        collected_input_mapping = {}
        collected_output_mapping = {}

        for stage in multi_stage.stages:
            for do_method in stage.doMethods:
                do_method_name = "DoMethod_" + str(do_method.doMethodID)
                extent_start, extent_end, _ = self.visit_interval(do_method.interval)
                do_method_name += "(%s:%s)" % (extent_start, extent_end)

                if interval[0] != extent_start or interval[1] != extent_end:
                    continue

                for stmt_access in do_method.stmtaccesspairs:
                    state = sub_sdfg.add_state("state_" + str(self.state_counter_))
                    self.state_counter_ += 1
                    # check if this if is required
                    if last_state_in_multi_stage is not None:
                        sub_sdfg.add_edge(last_state_in_multi_stage, state, dace.InterstateEdge())

                    # Creation of the Memlet in the state
                    self.current_stmt_access_ = stmt_access
                    input_memlets = {}
                    output_memlets = {}

                    for key in stmt_access.accesses.readAccess:
                        # since keys with negative ID's are *only* literals, we can skip those
                        if key < 0:
                            continue
                        f_name = self.metadata_.accessIDToName[key]
                        i_extent = stmt_access.accesses.readAccess[key].extents[0]
                        j_extent = stmt_access.accesses.readAccess[key].extents[1]
                        k_extent = stmt_access.accesses.readAccess[key].extents[2]
                        if key not in self.metadata_.globalVariableIDs:
                            access_pattern = (
                                "j+"
                                + str(j_extent.minus)
                                + ":j+"
                                + str(j_extent.plus)
                                + "+1"
                                + ","
                                + str(k_extent.minus)
                                + ":"
                                + str(k_extent.plus)
                                + "+1,"
                                + "i+"
                                + str(i_extent.minus)
                                + ":i+"
                                + str(i_extent.plus)
                                + "+1"
                            )
                        else:
                            access_pattern = "0"

                        # we promote every local variable to a temporary:
                        if f_name not in self.dataTokens_:
                            # add the transient to the top level sdfg
                            self.dataTokens_[f_name] = sdfg.add_array(
                                f_name + "_t", shape=[J, K + 1, I], dtype=data_type
                            )

                            # add the transient to the sub_sdfg:
                            if "S_" + f_name not in sub_sdfg_arrays:
                                sub_sdfg_arrays["S_" + f_name] = sub_sdfg.add_array(
                                    "S_" + f_name, shape=[J, K + 1, I], dtype=data_type
                                )

                        # create the memlet to create the mapped stmt
                        input_memlets[f_name + "_input"] = dace.Memlet.simple("S_" + f_name, access_pattern)

                        # add the field to the sub-sdfg as an array
                        if "S_" + f_name not in sub_sdfg_arrays:
                            sub_sdfg_arrays["S_" + f_name] = sub_sdfg.add_array(
                                "S_" + f_name, shape=[J, K + 1, I], dtype=data_type
                            )

                        # collection of all the input fields for the memlet paths outside the sub-sdfg
                        collected_input_mapping["S_" + f_name] = f_name + "_t"

                    for key in stmt_access.accesses.writeAccess:
                        f_name = self.metadata_.accessIDToName[key]

                        i_extent = stmt_access.accesses.writeAccess[key].extents[0]
                        j_extent = stmt_access.accesses.writeAccess[key].extents[1]
                        k_extent = stmt_access.accesses.writeAccess[key].extents[2]

                        access_pattern = (
                            "j+"
                            + str(j_extent.minus)
                            + ":j+"
                            + str(j_extent.plus)
                            + "+1"
                            + ","
                            + str(k_extent.minus)
                            + ":"
                            + str(k_extent.plus)
                            + "+1,"
                            + "i+"
                            + str(i_extent.minus)
                            + ":i+"
                            + str(i_extent.plus)
                            + "+1"
                        )

                        # we promote every local variable to a temporary:
                        if f_name not in self.dataTokens_:
                            # add the transient to the top level sdfg
                            self.dataTokens_[f_name] = sdfg.add_array(
                                f_name + "_t", shape=[J, K + 1, I], dtype=data_type
                            )

                            # add the transient to the sub_sdfg:
                            if "S_" + f_name not in sub_sdfg_arrays:
                                sub_sdfg_arrays["S_" + f_name] = sub_sdfg.add_array(
                                    "S_" + f_name, shape=[J, K + 1, I], dtype=data_type
                                )

                        # create the memlet
                        output_memlets[f_name] = dace.Memlet.simple("S_" + f_name, access_pattern)

                        # add the field to the sub-sdfg as an array
                        if "S_" + f_name not in sub_sdfg_arrays:
                            sub_sdfg_arrays["S_" + f_name] = sub_sdfg.add_array(
                                "S_" + f_name, shape=[J, K + 1, I], dtype=data_type
                            )

                        # collection of all the output fields for the memlet paths outside the sub-sdfg
                        collected_output_mapping["S_" + f_name] = f_name + "_t"

                    stmt_str = ""

                    stmt_str += self.visit_statement(stmt_access)

                    if stmt_str:
                        # adding input to every input-field for separation:
                        if __debug__:
                            print("before inout transformation")
                            print(stmt_str)
                        tree = ast.parse(stmt_str)
                        output_stmt = astunparse.unparse(RenameInput().visit(tree))

                        if __debug__:
                            print("after inout transformation")
                            print(output_stmt)

                        stmt_str = output_stmt

                        if __debug__:
                            print("this is the stmt-str:")
                            print(stmt_str)
                            print("in-mem")
                            print(input_memlets)
                            print("out-mem")
                            print(output_memlets)

                        # The memlet is only in ijk if the do-method is parallel, otherwise we have a loop and hence
                        # the maps are ij-only
                        map_range = dict(j="halo_size:J-halo_size", i="halo_size:I-halo_size")
                        state.add_mapped_tasklet(
                            "statement", map_range, input_memlets, stmt_str, output_memlets, external_edges=True
                        )

                    # set the state  to be the last one to connect them
                    self.last_state_in_multi_stage = state
                    if last_state is not None:
                        sub_sdfg.add_edge(last_state, state, dace.InterstateEdge())
                    last_state = state

        me_k, mx_k = multi_stage_state.add_map("kmap", dict(k="%s:%s" % (extent_start, extent_end)))
        # fill the sub-sdfg's {in_set} {out_set}
        input_set = collected_input_mapping.keys()
        output_set = collected_output_mapping.keys()
        nested_sdfg = multi_stage_state.add_nested_sdfg(sub_sdfg, sdfg, input_set, output_set)

        # add the reads and the input memlet path : read - me_k - nsdfg
        for k, v in collected_input_mapping.items():
            read = multi_stage_state.add_read(v)
            multi_stage_state.add_memlet_path(
                read,
                me_k,
                nested_sdfg,
                memlet=dace.Memlet.simple(v, "0:J, k, 0:I"),
                dst_conn=k,
            )
        # add the writes and the output memlet path : nsdfg - mx_k - write
        for k, v in collected_output_mapping.items():
            write = multi_stage_state.add_write(v)
            multi_stage_state.add_memlet_path(
                nested_sdfg,
                mx_k,
                write,
                memlet=dace.Memlet.simple(v, "0:J, k, 0:I"),
                src_conn=k,
            )

        if self.last_state_ is not None:
            sdfg.add_edge(self.last_state_, multi_stage_state, dace.InterstateEdge())

        return multi_stage_state

    def generate_loop(self, multi_stage, interval, loop_order):
        first_interval_state = None
        # This is the state previous to this ms
        prev_state = self.last_state_
        for stage in multi_stage.stages:
            for do_method in stage.doMethods:
                # Generate the name of the Do-Method
                do_method_name = "DoMethod_" + str(do_method.doMethodID)
                extent_start, extent_end, _ = self.visit_interval(do_method.interval)
                do_method_name += "(%s:%s)" % (extent_start, extent_end)
                # since we only want to generate stmts for the Do-Methods that are matching the interval, we're ignoring
                # the other ones
                if interval[0] != extent_start or interval[1] != extent_end:
                    continue

                for stmt_access in do_method.stmtaccesspairs:
                    # A State for every stmt makes sure they can be sequential
                    state = sdfg.add_state("state_" + str(self.state_counter_))
                    self.state_counter_ += 1
                    if first_interval_state is None:
                        first_interval_state = state
                    else:
                        sdfg.add_edge(self.last_state_, state, dace.InterstateEdge())

                    # Creation of the Memlet in the state
                    self.current_stmt_access_ = stmt_access
                    input_memlets = {}
                    output_memlets = {}

                    for key in stmt_access.accesses.readAccess:

                        # since keys with negative ID's are *only* literals, we can skip those
                        if key < 0:
                            continue

                        f_name = self.metadata_.accessIDToName[key]

                        i_extent = stmt_access.accesses.readAccess[key].extents[0]
                        j_extent = stmt_access.accesses.readAccess[key].extents[1]
                        k_extent = stmt_access.accesses.readAccess[key].extents[2]

                        # create the access extent for the read-Access
                        if key not in self.metadata_.globalVariableIDs:
                            access_pattern = (
                                "j+"
                                + str(j_extent.minus)
                                + ":j+"
                                + str(j_extent.plus)
                                + "+1"
                                + ",k+"
                                + str(k_extent.minus)
                                + ":k+"
                                + str(k_extent.plus)
                                + "+1,"
                                + "i+"
                                + str(i_extent.minus)
                                + ":i+"
                                + str(i_extent.plus)
                                + "+1"
                            )
                        else:
                            access_pattern = "0"

                        # we promote every local variable to a temporary:
                        if f_name not in self.dataTokens_:
                            self.dataTokens_[f_name] = sdfg.add_transient(
                                f_name + "_t", shape=[J, K + 1, I], dtype=data_type
                            )

                        input_memlets[f_name + "_input"] = dace.Memlet.simple(f_name + "_t", access_pattern)

                    for key in stmt_access.accesses.writeAccess:

                        f_name = self.metadata_.accessIDToName[key]

                        i_extent = stmt_access.accesses.writeAccess[key].extents[0]
                        j_extent = stmt_access.accesses.writeAccess[key].extents[1]
                        k_extent = stmt_access.accesses.writeAccess[key].extents[2]

                        access_pattern = (
                            "j+"
                            + str(j_extent.minus)
                            + ":j+"
                            + str(j_extent.plus)
                            + "+1"
                            + ",k+"
                            + str(k_extent.minus)
                            + ":k+"
                            + str(k_extent.plus)
                            + "+1,"
                            + "i+"
                            + str(i_extent.minus)
                            + ":i+"
                            + str(i_extent.plus)
                            + "+1"
                        )

                        # we promote every local variable to a temporary:
                        if f_name not in self.dataTokens_:
                            self.dataTokens_[f_name] = sdfg.add_transient(
                                f_name + "_t", shape=[J, K + 1, I], dtype=data_type
                            )

                        output_memlets[f_name] = dace.Memlet.simple(f_name + "_t", access_pattern)

                    # Create the statement
                    stmt_str = ""
                    stmt_str += self.visit_statement(stmt_access)

                    if stmt_str:
                        # adding input to every input-field for separation:
                        if __debug__:
                            print("before inout transformation")
                            print(stmt_str)

                        tree = ast.parse(stmt_str)
                        output_stmt = astunparse.unparse(RenameInput().visit(tree))

                        if __debug__:
                            print("after inout transformation")
                            print(output_stmt)

                        stmt_str = output_stmt

                        if __debug__:
                            print("this is the stmt-str:")
                            print(stmt_str)
                            print("in-mem")
                            print(input_memlets)
                            print("out-mem")
                            print(output_memlets)

                        # Since we're in a sequential loop, we only need a map in i and j
                        map_range = dict(j="halo_size:J-halo_size", i="halo_size:I-halo_size")

                        state.add_mapped_tasklet(
                            "statement", map_range, input_memlets, stmt_str, output_memlets, external_edges=True
                        )

                    # set the state to be the last one to connect to it
                    self.last_state_ = state

        if __debug__:
            print("loop order is: %i" % loop_order)
        if loop_order == 0:
            _, _, last_state = sdfg.add_loop(
                prev_state,
                first_interval_state,
                None,
                "k",
                interval[0],
                "k < %s" % interval[1],
                "k + 1",
                self.last_state_,
            )
            return last_state
        elif loop_order == 1:
            _, _, last_state = sdfg.add_loop(
                prev_state,
                first_interval_state,
                None,
                "k",
                interval[0],
                "k > %s" % interval[1],
                "k - 1",
                self.last_state_,
            )
            return last_state
        else:
            assert "wrong usage"


if __name__ == "__main__":
    print("==== Program start ====")

    parser = argparse.ArgumentParser(
        description="""Deserializes a google protobuf file encoding an HIR example and traverses the AST printing a
                    DSL code with the user equations"""
    )
    parser.add_argument("hirfile", type=argparse.FileType("rb"), help="google protobuf HIR file")
    args = vars(parser.parse_args())

    stencilInstantiation = IIR_pb2.StencilInstantiation()

    print("Parsing file `%s`" % args["hirfile"].name)

    stencilInstantiation.ParseFromString(args["hirfile"].read())
    args["hirfile"].close()

    print("Parsing successful")

    metadata = stencilInstantiation.metadata
    print("original file was `%s`" % stencilInstantiation.filename)

    print("Generate SDFG for `%s`" % metadata.stencilName)

    fields = {}
    for a in metadata.APIFieldIDs:
        fields[metadata.accessIDToName[a]] = dace.ndarray([J, K + 1, I], dtype=data_type)

    sdfg = dace.SDFG("IIRToSDFG")

    loopFields = {}
    for a in metadata.APIFieldIDs:
        field_name = metadata.accessIDToName[a]
        sdfg.add_array("c" + field_name + "_t", shape=[J, K + 1, I], dtype=data_type)

    des = TaskletBuilder(stencilInstantiation.metadata)

    des.build_data_tokens(sdfg)

    des.fill_globals()

    for stencil in stencilInstantiation.internalIR.stencils:
        des.visit_stencil(stencil)

    sdfg.fill_scope_connectors()

    nodes = list(sdfg.nodes())
    if __debug__:
        print("number of states generated: %d" % len(nodes))

    print("SDFG generation successful")

    sdfg.draw_to_file("before_transformation.dot")

    pickle.dump(sdfg, open("before.sdfg", "wb"))

    sdfg.apply_strict_transformations()
    sdfg.draw_to_file("final.dot")

    print("Strict transformations applied, state graphs before and after are drawn")

    pickle.dump(sdfg, open("after.sdfg", "wb"))

    print("sdfg stored in example.sdfg")

    sdfg.validate()
    print("sdfg validated")

    sdfg.compile()

    print("compilation successful")
