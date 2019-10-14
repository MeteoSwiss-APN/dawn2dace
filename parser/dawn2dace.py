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


class Interval:
    """Represents an interval [begin, end)"""

    def __init__(self, begin, end, sort_key):
        self.begin = begin
        self.end = end
        self.sort_key = sort_key

    def __str__(self):
        return "{}:{}".format(self.begin, self.end)


class MemoryExtent1D:
    def __init__(self, minus: int, plus: int):
        self.minus = minus
        self.plus = plus

    def expand_with(self, o):
        self.minus = min(self.minus, o.minus)
        self.plus = max(self.plus, o.plus)


class MemoryExtent3D:
    def __init__(self, i: MemoryExtent1D, j: MemoryExtent1D, k: MemoryExtent1D):
        self.i = i
        self.j = j
        self.k = k

    def expand_with(self, o):
        self.i.expand_with(o.i)
        self.j.expand_with(o.j)
        self.k.expand_with(o.k)


class Memlet:
    def __init__(self, name: str, extent):
        self.name = name
        self.extent = extent

    def to_dace(self):
        if self.extent is None:
            access_pattern = "0"
        else:
            access_pattern = "j+{}:j+{}+1,{}:{}+1,i+{}:i+{}+1".format(
                self.extent.j.minus, self.extent.j.plus,
                self.extent.k.minus, self.extent.k.plus,
                self.extent.i.minus, self.extent.i.plus)
        return dace.Memlet.simple("S_" + self.name, access_pattern)


I = dace.symbol("I")
J = dace.symbol("J")
K = dace.symbol("K")
halo_size = dace.symbol("haloSize")
data_type = dace.float64

class RenameInput(ast.NodeTransformer):
    @staticmethod
    def visit_Name(node):
        if isinstance(node.ctx, ast.Load):
            node.id += "_input"
        return node


class TaskletBuilder:
    def __init__(self, _metadata):
        self.metadata_ = _metadata
        self.dataTokens_ = {}
        self.current_stmt_access_ = None
        self.state_counter_ = -1  # Only used within 'CreateUID()'
        self.last_state_ = None

    def CreateUID(self):
        """Creates unique identification number"""
        self.state_counter_ += 1
        return self.state_counter_

    def fill_globals(self):
        for fID in self.metadata_.globalVariableIDs:
            f_name = self.metadata_.accessIDToName[fID]
            self.dataTokens_[f_name] = sdfg.add_scalar(f_name + "_t", dace.float32)

    @staticmethod
    def visit_builtin_type(builtin_type):
        id = builtin_type.type_id
        if id == 1:
            return "auto"
        if id == 2:
            return "bool"
        if id == 3:
            return "int"
        if id == 4:
            return "float"
        raise ValueError("Builtin type not supported")

    def visit_unary_operator(self, expr):
        return "{} ({})".format(
            expr.op,
            self.visit_expr(expr.operand)
        )

    def visit_binary_operator(self, expr):
        return "({}) {} ({})".format(
            self.visit_expr(expr.left),
            expr.op,
            self.visit_expr(expr.right)
        )

    def visit_assignment_expr(self, expr):
        return "{} {} ({})".format(
            self.visit_expr(expr.left),
            expr.op,
            self.visit_expr(expr.right)
        )

    def visit_ternary_operator(self, expr):
        return "( ({}) ? ({}) : ({}))".format(
            self.visit_expr(expr.cond),
            self.visit_expr(expr.left),
            self.visit_expr(expr.right)
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
        ex = expr.WhichOneof("expr")
        if ex == "unary_operator":
            return self.visit_unary_operator(expr.unary_operator)
        if ex == "binary_operator":
            return self.visit_binary_operator(expr.binary_operator)
        if ex == "assignment_expr":
            return self.visit_assignment_expr(expr.assignment_expr)
        if ex == "ternary_operator":
            return self.visit_ternary_operator(expr.ternary_operator)
        if ex == "fun_call_expr":
            return self.visit_fun_call_expr(expr.fun_call_expr)
        if ex == "stencil_fun_call_expr":
            raise ValueError("non supported expression")
        if ex == "stencil_fun_arg_expr":
            raise ValueError("non supported expression")
        if ex == "var_access_expr":
            return self.visit_var_access_expr(expr.var_access_expr)
        if ex == "field_access_expr":
            return self.visit_field_access_expr(expr.field_access_expr)
        if ex == "literal_access_expr":
            return self.visit_literal_access_expr(expr.literal_access_expr)
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
        st = stmt.WhichOneof("stmt")
        if st == "var_decl_stmt":
            return self.visit_var_decl_stmt(stmt.var_decl_stmt)
        if st == "expr_stmt":
            return self.visit_expr_stmt(stmt.expr_stmt)
        if st == "if_stmt":
            return self.visit_if_stmt(stmt.if_stmt)
        if st == "block_stmt":
            return self.visit_block_stmt(stmt.block_stmt)
        raise ValueError("Stmt not supported :" + stmt.WhichOneof("stmt"))

    @staticmethod
    def visit_interval(interval):
        """
        Converts a Dawn-interval into a Dawn2Dice-interval.
        Warning: Only works for dimension 'K', which might be sufficient for COSMO.
        """
        if interval.WhichOneof("LowerLevel") == "special_lower_level":
            if interval.special_lower_level == 0:
                begin = "0"
                sort_key = 0
            else:
                begin = "K-1"
                sort_key = 10000 - 1
        elif interval.WhichOneof("LowerLevel") == "lower_level":
            begin = str(interval.lower_level)
            sort_key = interval.lower_level

        begin += " + " + str(interval.lower_offset)
        sort_key += interval.lower_offset

        if interval.WhichOneof("UpperLevel") == "special_upper_level":
            if interval.special_upper_level == 0:
                end = "0"
            else:
                end = "K-1"
        elif interval.WhichOneof("UpperLevel") == "upper_level":
            end = str(interval.upper_level)

        end += " + " + str(interval.upper_offset)
        end += "+1"  # since python interval are open we need to add 1

        return Interval(begin, end, sort_key)

    def visit_statement(self, stmt):
        return self.visit_body_stmt(stmt.ASTStmt)

    def visit_multi_stage(self, ms):

        # gather intervals in K dimension.
        intervals = set()
        for stage in ms.stages:
            for do_method in stage.doMethods:
                intervals.add(self.visit_interval(do_method.interval))

        intervals = list(intervals)
        intervals.sort(key=lambda i: i.sort_key, reverse=(ms.loopOrder == 1))

        if __debug__:
            print("list of all the intervals:")
            for interval in intervals:
                print("[{}]".format(interval))

        # generate the multistage for every interval (in loop order)
        for interval in intervals:
            self.generate_multistage(ms.loopOrder, ms, interval)

    def visit_stencil(self, stencil_):
        for ms in stencil_.multiStages:
            self.visit_multi_stage(ms)

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
            self.generate_parallel(multi_stage, interval)
            #
            #
            # change this back to parallel once tal figured out the problem with the generated sdfg
            #
            #
            #
            #
            # self.generate_loop(multi_stage, interval, 0)
        else:
            self.generate_loop(multi_stage, interval, loop_order)
    
    def getMemlets(self, access, memlet_prefix:str='', memlet_suffix:str='', dace_prefix:str='', dace_suffix:str=''):
        memlets = {}
        for key in access:
            if key < 0:
                continue # since keys with negative IDs are *only* literals, we can skip those

            if key in self.metadata_.globalVariableIDs:
                access_pattern = "0"
            else:
                i = access[key].extents[0]
                j = access[key].extents[1]
                k = access[key].extents[2]
                access_pattern = "j+{}:j+{}+1,{}:{}+1,i+{}:i+{}+1".format(
                    j.minus, j.plus,
                    k.minus, k.plus,  # TODO: replace with (0, k.plus - k.minus)
                    i.minus, i.plus)

            field_name = self.metadata_.accessIDToName[key]
            memlets[memlet_prefix + field_name + memlet_suffix] = dace.Memlet.simple(dace_prefix + field_name + dace_suffix, access_pattern)
        return memlets

    def addToMapping(self, access, tasklet_path_map, dace_sub_sdfg, sub_sdfgs):
        for key in access:
            if key < 0:
                continue # since keys with negative IDs are *only* literals, we can skip those

            # we promote every local variable to a temporary:
            field_name = self.metadata_.accessIDToName[key]
            if field_name not in self.dataTokens_:
                # add the transient to the top level sdfg
                self.dataTokens_[field_name] = sdfg.add_array(
                    field_name + "_t", shape=[J, K + 1, I], dtype=data_type
                    )

            # add the field to the sub-sdfg as an array
            if "S_" + field_name not in sub_sdfgs:
                sub_sdfgs["S_" + field_name] = dace_sub_sdfg.add_array(
                    "S_" + field_name, shape=[J, K + 1, I], dtype=data_type
                    )

            # collection of all the input fields for the memlet paths outside the sub-sdfg
            tasklet_path_map["S_" + field_name] = field_name + "_t"

    def generate_parallel(self, multi_stage, interval):
        multi_stage_state = sdfg.add_state("state_{}".format(self.CreateUID()))

        dace_sub_sdfg = dace.SDFG("ms_subsdfg{}".format(self.CreateUID()))
        sub_sdfgs = {}

        last_state_in_multi_stage = None
        last_state = None
        # to connect them we need all input and output names
        tasklet_input = {} # maps tasklet input fields to path
        tasklet_output = {} # maps tasklet output fields to path

        for stage in multi_stage.stages:
            for do_method in stage.doMethods:
                extent = self.visit_interval(do_method.interval)
                do_method_name = "DoMethod_{}({})".format(do_method.doMethodID, extent)

                if interval.begin != extent.begin or interval.end != extent.end:
                    continue

                for stmt_access in do_method.stmtaccesspairs:
                    state = dace_sub_sdfg.add_state("state_{}".format(self.CreateUID()))
                    # TODO: check if this if is required
                    if last_state_in_multi_stage is not None:
                        dace_sub_sdfg.add_edge(last_state_in_multi_stage, state, dace.InterstateEdge())

                    # Creation of the Memlet in the state
                    self.current_stmt_access_ = stmt_access
                    input_memlets = self.getMemlets(stmt_access.accesses.readAccess, dace_prefix="S_", memlet_suffix="_input")
                    output_memlets = self.getMemlets(stmt_access.accesses.writeAccess, dace_prefix="S_")

                    self.addToMapping(stmt_access.accesses.readAccess, tasklet_input, dace_sub_sdfg, sub_sdfgs)
                    self.addToMapping(stmt_access.accesses.writeAccess, tasklet_output, dace_sub_sdfg, sub_sdfgs)

                    stmt_str = self.visit_statement(stmt_access)

                    if stmt_str:
                        # adding input to every input-field for separation:
                        if __debug__:
                            print("before inout transformation")
                            print(stmt_str)
                        
                        tree = ast.parse(stmt_str)
                        stmt_str = astunparse.unparse(RenameInput().visit(tree))

                        if __debug__:
                            print("after inout transformation")
                            print(stmt_str)
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

                    # set the state to be the last one to connect them
                    if last_state is not None:
                        dace_sub_sdfg.add_edge(last_state, state, dace.InterstateEdge())
                    last_state = state

        map_entry_k, map_exit_k = multi_stage_state.add_map("kmap", dict(k=str(extent)))

        # fill the sub-sdfg's {in_set} {out_set}
        input_set = tasklet_input.keys()
        output_set = tasklet_output.keys()
        nested_sdfg = multi_stage_state.add_nested_sdfg(dace_sub_sdfg, sdfg, input_set, output_set)

        # add the reads and the input memlet path : read -> map_entry_k -> nested_sdfg
        for tasklet_field, path in tasklet_input.items():
            read = multi_stage_state.add_read(path)
            #self.dataTokens_[tasklet_field].shape.
            multi_stage_state.add_memlet_path(
                read,
                map_entry_k,
                nested_sdfg,
                memlet=dace.Memlet.simple(path, "0:J, k, 0:I"),
                dst_conn=tasklet_field,
            )
        # add the writes and the output memlet path : nested_sdfg -> map_exit_k -> write
        for tasklet_field, path in tasklet_output.items():
            write = multi_stage_state.add_write(path)
            multi_stage_state.add_memlet_path(
                nested_sdfg,
                map_exit_k,
                write,
                memlet=dace.Memlet.simple(path, "0:J, k, 0:I"),
                src_conn=tasklet_field,
            )

        if self.last_state_ is not None:
            sdfg.add_edge(self.last_state_, multi_stage_state, dace.InterstateEdge())

        self.last_state_ = multi_stage_state

    
    def addToMapping2(self, access):
        for key in access:
            if key < 0:
                continue # since keys with negative IDs are *only* literals, we can skip those

            # we promote every local variable to a temporary:
            field_name = self.metadata_.accessIDToName[key]
            if field_name not in self.dataTokens_:
                # add the transient to the top level sdfg
                self.dataTokens_[field_name] = sdfg.add_array(field_name + "_t", shape=[J, K + 1, I], dtype=data_type)

    def generate_loop(self, multi_stage, interval, loop_order):
        first_interval_state = None
        # This is the state previous to this ms
        prev_state = self.last_state_
        for stage in multi_stage.stages:
            for do_method in stage.doMethods:
                extent = self.visit_interval(do_method.interval)
                do_method_name = "DoMethod_{}({})".format(do_method.doMethodID, extent)
                # since we only want to generate stmts for the Do-Methods that are matching the interval, we're ignoring
                # the other ones
                if interval.begin != extent.begin or interval.end != extent.end:
                    continue

                for stmt_access in do_method.stmtaccesspairs:
                    # A State for every stmt makes sure they can be sequential
                    state = sdfg.add_state("state_{}".format(self.CreateUID()))
                    if first_interval_state is None:
                        first_interval_state = state
                    else:
                        sdfg.add_edge(self.last_state_, state, dace.InterstateEdge())

                    # Creation of the Memlet in the state
                    self.current_stmt_access_ = stmt_access
                    input_memlets = self.getMemlets(stmt_access.accesses.readAccess, dace_suffix="_t", memlet_suffix="_input")
                    output_memlets = self.getMemlets(stmt_access.accesses.writeAccess, dace_suffix="_t")

                    self.addToMapping2(stmt_access.accesses.readAccess)
                    self.addToMapping2(stmt_access.accesses.writeAccess)

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
            self.last_state_ = last_state
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
            self.last_state_ = last_state
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
    sdfg.save("final.sdfg", use_pickle=False)

    print(sdfg.signature(with_types=False))

    print("Strict transformations applied, state graphs before and after are drawn")

    pickle.dump(sdfg, open("after.sdfg", "wb"))

    print("sdfg stored in example.sdfg")

    sdfg.validate()
    print("sdfg validated")

    sdfg.compile()

    print("compilation successful")
