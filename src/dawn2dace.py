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
from IIR_AST import *

class Renamer(IIR_Transformer):
    def __init__(self, ids:dict, suffix:str):
        self.ids = ids
        self.suffix = suffix

    def visit_FieldAccessExpr(self, expr):
        if expr.data.accessID.value in self.ids:
            expr.name += self.suffix
        return expr

def RenameVariables(stencils: list):
    """
    Renames all variables that are read from by adding a suffix '_in'.
    Renames all variables that are written to by adding a suffix '_out'.
    """
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        stmt.code = Renamer(stmt.reads, '_in').visit(stmt.code)
                        stmt.code = Renamer(stmt.writes, '_out').visit(stmt.code)


class IJ_Mapper(IIR_Transformer):
    def __init__(self, transfer:dict):
        self.transfer = transfer

    def visit_FieldAccessExpr(self, expr):
        id = expr.data.accessID.value
        if id in self.transfer:
            if self.transfer[id].i.begin != self.transfer[id].i.end:
                expr.cartesian_offset.i_offset -= self.transfer[id].i.begin
            if self.transfer[id].j.begin != self.transfer[id].j.end:
                expr.cartesian_offset.j_offset -= self.transfer[id].j.begin
        return expr

def AccountForIJMap(stencils: list):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        stmt.code = IJ_Mapper(stmt.reads).visit(stmt.code)


class K_Mapper(IIR_Transformer):
    def __init__(self, k_offset:int, transfer:dict):
        self.k_offset = k_offset
        self.transfer = transfer

    def visit_FieldAccessExpr(self, expr):
        id = expr.data.accessID.value
        if id in self.transfer:
            expr.vertical_offset += self.k_offset
        return expr

def AccountForKMap(stencils: list):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            k_min = multi_stage.GetMinReadInK()
            k_max = multi_stage.GetMaxReadInK()
            multi_stage.lower_k = k_min
            multi_stage.upper_k = k_max
            if k_min != 0:
                for stage in multi_stage.stages:
                    for do_method in stage.do_methods:
                        for stmt in do_method.statements:
                            for _, read in stmt.reads.items():
                                read.offset(k = -k_min)
                            stmt.code = K_Mapper(-k_min, stmt.reads).visit(stmt.code)


class DimensionalReducer(IIR_Transformer):
    def __init__(self, transfer:dict):
        self.transfer = transfer

    def visit_FieldAccessExpr(self, expr):
        id = expr.data.accessID.value
        if id in self.transfer:
            if self.transfer[id].i.begin == self.transfer[id].i.end:
                expr.cartesian_offset.i_offset = -1000
            if self.transfer[id].j.begin == self.transfer[id].j.end:
                expr.cartesian_offset.j_offset = -1000
            if self.transfer[id].k.begin == self.transfer[id].k.end:
                 expr.vertical_offset = -1000
        return expr

def RemoveUnusedDimensions(stencils: list):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        DimensionalReducer(stmt.reads).visit(stmt.code)
                        DimensionalReducer(stmt.writes).visit(stmt.code)


def UnparseCode(stencils: list):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        stmt.code = Unparser().unparse_body_stmt(stmt.code)
                        print(stmt.code)

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

    imp = Importer(id_resolver)
    stencils = imp.Import_Stencils(stencilInstantiation.internalIR.stencils)


    RenameVariables(stencils)
    AccountForIJMap(stencils)
    AccountForKMap(stencils)
    RemoveUnusedDimensions(stencils)
    UnparseCode(stencils)

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

    
