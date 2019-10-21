from __future__ import print_function


import dace
import argparse
import ast
import os
import pickle
import sys
import astunparse
from NameResolver import NameResolver
from StatementVisitor import StatementVisitor

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "build", "gen", "iir_specification"))
)

import IIR_pb2

def CreateUID() -> int:
    """ Creates unique identification numbers. """
    if not hasattr(CreateUID, "counter"):
        CreateUID.counter = 0
    CreateUID.counter += 1
    return CreateUID.counter

I = dace.symbol("I")
J = dace.symbol("J")
K = dace.symbol("K")
halo_size = dace.symbol("haloSize")
data_type = dace.float64


class InputRenamer(ast.NodeTransformer):
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            node.id += "_input"
        return node


class TaskletBuilder:
    def __init__(self, _metadata, name_resolver:NameResolver):
        self.get_name = name_resolver
        self.metadata_ = _metadata
        self.dataTokens_ = {}
        self.last_state_ = None

    def visit_statement(self, stmt_access_pair) -> str:
        visitor = StatementVisitor(self.get_name, stmt_access_pair.accesses)
        return visitor.visit_body_stmt(stmt_access_pair.ASTStmt)

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

    def generate_multistage(self, loop_order, multi_stage, interval):
        if loop_order == 2:
            return self.generate_parallel(multi_stage, interval)
        else:
            return self.generate_loop(multi_stage, interval, loop_order)

    def generate_parallel(self, multi_stage, interval):
        multi_stage_state = sdfg.add_state("state_" + str(CreateUID()))
        sub_sdfg = dace.SDFG("ms_subsdfg" + str(CreateUID()))
        sub_sdfg_arrays = {}
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
                    state = sub_sdfg.add_state("state_" + str(CreateUID()))
                    # check if this if is required
                    if last_state_in_multi_stage is not None:
                        sub_sdfg.add_edge(last_state_in_multi_stage, state, dace.InterstateEdge())

                    # Creation of the Memlet in the state
                    input_memlets = {}
                    output_memlets = {}

                    for key in stmt_access.accesses.readAccess:
                        # since keys with negative ID's are *only* literals, we can skip those
                        if key < 0:
                            continue
                        f_name = self.get_name.FromAccessID(key)
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
                        f_name = self.get_name.FromAccessID(key)

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
                        output_stmt = astunparse.unparse(InputRenamer().visit(tree))

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
                    state = sdfg.add_state("state_" + str(CreateUID()))
                    if first_interval_state is None:
                        first_interval_state = state
                    else:
                        sdfg.add_edge(self.last_state_, state, dace.InterstateEdge())

                    # Creation of the Memlet in the state
                    input_memlets = {}
                    output_memlets = {}

                    for key in stmt_access.accesses.readAccess:

                        # since keys with negative ID's are *only* literals, we can skip those
                        if key < 0:
                            continue

                        f_name = self.get_name.FromAccessID(key)

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

                        f_name = self.get_name.FromAccessID(key)

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
                        output_stmt = astunparse.unparse(InputRenamer().visit(tree))

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

    name_resolver = NameResolver(
        metadata.accessIDToName,
        metadata.exprIDToAccessID,
        metadata.stmtIDToAccessID
        )

    fields = {}
    for a in metadata.APIFieldIDs:
        fields[metadata.accessIDToName[a]] = dace.ndarray([J, K + 1, I], dtype=data_type)

    sdfg = dace.SDFG("IIRToSDFG")

    loopFields = {}
    for a in metadata.APIFieldIDs:
        field_name = metadata.accessIDToName[a]
        sdfg.add_array("c" + field_name + "_t", shape=[J, K + 1, I], dtype=data_type)

    des = TaskletBuilder(stencilInstantiation.metadata, name_resolver)

    for id in metadata.APIFieldIDs:
        name = name_resolver.FromAccessID(id)
        array = sdfg.add_array(name + "_t", shape=[J, K + 1, I], dtype=data_type)
        des.dataTokens_[name] = array

    for id in metadata.temporaryFieldIDs:
        name = name_resolver.FromAccessID(id)
        des.dataTokens_[name] = sdfg.add_transient(name + "_t", shape=[J, K + 1, I], dtype=data_type)

    for id in metadata.globalVariableIDs:
        name = name_resolver.FromAccessID(id)
        des.dataTokens_[name] = sdfg.add_scalar(name + "_t", data_type)

    for stencil in stencilInstantiation.internalIR.stencils:
        des.visit_stencil(stencil)

    sdfg.fill_scope_connectors()

    print("number of states generated: %d" % len(sdfg.nodes()))

    sdfg.save("untransformed.sdfg", use_pickle=False)
    print("SDFG generated.")

    sdfg.apply_strict_transformations()
    sdfg.save("transformed.sdfg", use_pickle=False)
    print("SDFG transformed strictly.")

    sdfg.validate()
    print("SDFG validated.")

    sdfg.compile()
    print("SDFG compiled.")
