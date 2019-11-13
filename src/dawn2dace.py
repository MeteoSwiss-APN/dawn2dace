import dace
import argparse
import ast
import os
import pickle
import sys
import astunparse
import IIR_pb2
from Intermediates import *
from Importer import Importer
from Exporter import *
from IdResolver import IdResolver
from Unparser import Unparser

def FixNegativeIndices(stencils: list):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            min = multi_stage.GetMinReadInK()
            if min < 0:
                for stage in multi_stage.stages:
                    for do_method in stage.do_methods:
                        for stmt in do_method.statements:
                            for read in stmt.reads:
                                read.offset(k = -min)
                            for write in stmt.writes:
                                write.offset(k = -min)

def IIR_str_to_SDFG(iir: str):
    stencilInstantiation = IIR_pb2.StencilInstantiation()
    stencilInstantiation.ParseFromString(iir)

    sdfg = dace.SDFG("IIRToSDFG")

    metadata = stencilInstantiation.metadata
    id_resolver = IdResolver(metadata.accessIDToName, metadata.APIFieldIDs, metadata.temporaryFieldIDs, metadata.globalVariableIDs)

    for id in metadata.APIFieldIDs:
        name = id_resolver.GetName(id)
        sdfg.add_array(name, shape=[J, K, I], dtype=data_type)

    for id in metadata.temporaryFieldIDs:
        name = id_resolver.GetName(id)
        sdfg.add_transient(name, shape=[J, K, I], dtype=data_type)

    for id in metadata.globalVariableIDs:
        name = id_resolver.GetName(id)
        sdfg.add_scalar(name, data_type)

    imp = Importer(id_resolver, metadata.globalVariableIDs)
    stencils = imp.Import_Stencils(stencilInstantiation.internalIR.stencils)


    #RenameInput(stencils)
    #FixNegativeIndices(stencils)
    #UnparseCode(stencils)

    exp = Exporter(id_resolver, sdfg)
    exp.Export_Stencils(stencils)

    sdfg.fill_scope_connectors()
    return sdfg

def IIR_file_to_SDFG_file(iir_file: str, sdfg_file: str):
    with open(iir_file) as f:
        iir = f.read()

    sdfg = IIR_str_to_SDFG(iir)

    sdfg.save(sdfg_file, use_pickle=False)

if __name__ == "__main__":
    print("==== Program start ====")

    parser = argparse.ArgumentParser(
        description="""Deserializes a google protobuf file encoding an HIR example and traverses the AST printing a
                    DSL code with the user equations"""
    )
    parser.add_argument("hirfile", type=argparse.FileType("rb"), help="google protobuf HIR file")
    args = vars(parser.parse_args())

    iir_str = args["hirfile"].read()

    sdfg = IIR_str_to_SDFG(iir_str)

    sdfg.save("untransformed.sdfg", use_pickle=False)
    print("SDFG generated.")

    #sdfg.apply_strict_transformations()
    #sdfg.save("transformed.sdfg", use_pickle=False)
    #print("SDFG transformed strictly.")

    sdfg.validate()
    print("SDFG validated.")

    sdfg.compile(output_file="libmine.so")
    print("SDFG compiled.")

    
