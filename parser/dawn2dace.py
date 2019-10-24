from __future__ import print_function

import dace
import argparse
import ast
import os
import pickle
import sys
import astunparse
from Intermedates import *
from Importer import Importer
from Exporter import *
from NameResolver import NameResolver
from StatementVisitor import StatementVisitor

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "build", "gen", "iir_specification"))
)

import IIR_pb2


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
    IIR_stencils = stencilInstantiation.internalIR.stencils
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

    for id in metadata.APIFieldIDs:
        name = name_resolver.FromAccessID(id)
        sdfg.add_array(name + "_t", shape=[J, K + 1, I], dtype=data_type)
        sdfg.add_array("c" + name + "_t", shape=[J, K + 1, I], dtype=data_type)

    for id in metadata.temporaryFieldIDs:
        name = name_resolver.FromAccessID(id)
        sdfg.add_transient(name + "_t", shape=[J, K + 1, I], dtype=data_type)

    for id in metadata.globalVariableIDs:
        name = name_resolver.FromAccessID(id)
        sdfg.add_scalar(name + "_t", data_type)

    imp = Importer(name_resolver, metadata.globalVariableIDs)
    exp = Exporter(name_resolver, sdfg)

    stencils = imp.Import_Stencils(IIR_stencils)
    exp.Export_Stencils(stencils)

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
