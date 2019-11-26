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

class Renamer(ast.NodeTransformer):
    def __init__(self):
        self.storemode = False

    def visit_Name(self, node):
        if self.storemode or isinstance(node.ctx, ast.Store):
            node.id += '_out'
        elif isinstance(node.ctx, ast.Load):
            node.id += '_in'
        return node

    def visit_Assign(self, node):
        self.storemode = True
        for target in node.targets:
            self.visit(target)
        self.storemode = False
        self.visit(node.value)
        return node

    def visit_AnnAssign(self, node):
        return self.visit_AugAssign(node)

    def visit_AugAssign(self, node):
        self.storemode = True
        self.visit(node.target)
        self.storemode = False
        self.visit(node.value)
        return node

def RenameVariables(stencils: list, id_resolver):
    """
    Renames all variables that are read from by adding a suffix '_in'.
    Renames all variables that are written to by adding a suffix '_out'.
    """
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        tree = ast.parse(stmt.code)
                        stmt.code = astunparse.unparse(Renamer().visit(tree))

                        print(stmt.code)

class IJ_Mapper(IIR_Transformer):
    def __init__(self, transfer:dict):
        self.transfer = transfer

    def visit_FieldAccessExpr(self, expr):
        id = expr.data.accessID.value
        if id in self.transfer:
            mem_acc = self.transfer[id]
            if mem_acc.i.lower != mem_acc.i.upper:
                expr.cartesian_offset.i_offset -= mem_acc.i.lower
            if mem_acc.j.lower != mem_acc.j.upper:
                expr.cartesian_offset.j_offset -= mem_acc.j.lower
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
            span = multi_stage.GetReadSpan()
            k_min = span.k.lower
            k_max = span.k.upper
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
    def __init__(self, id_resolver:IdResolver, transfer:dict):
        self.id_resolver = id_resolver
        self.transfer = transfer

    def visit_FieldAccessExpr(self, expr):
        id = expr.data.accessID.value
        if id in self.transfer:
            name = self.id_resolver.GetName(id)
            dims = self.id_resolver.GetDimensions(id)
            mem_acc = self.transfer[id]

            if (mem_acc.i.lower == mem_acc.i.upper) or not dims[0]:
                expr.cartesian_offset.i_offset = -1000
            if (mem_acc.j.lower == mem_acc.j.upper) or not dims[1]:
                expr.cartesian_offset.j_offset = -1000
            if (mem_acc.k.lower == mem_acc.k.upper) or not dims[2]:
                 expr.vertical_offset = -1000
        return expr

def RemoveUnusedDimensions(id_resolver:IdResolver, stencils: list):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        DimensionalReducer(id_resolver, stmt.reads).visit(stmt.code)
                        DimensionalReducer(id_resolver, stmt.writes).visit(stmt.code)


def UnparseCode(stencils: list):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        stmt.code = Unparser().unparse_body_stmt(stmt.code)

def IIR_str_to_SDFG(iir: str):
    stencilInstantiation = IIR_pb2.StencilInstantiation()
    stencilInstantiation.ParseFromString(iir)

    sdfg = dace.SDFG("IIRToSDFG")

    metadata = stencilInstantiation.metadata
    id_resolver = IdResolver(
        metadata.accessIDToName,
        metadata.APIFieldIDs,
        metadata.temporaryFieldIDs,
        metadata.globalVariableIDs,
        metadata.fieldIDtoLegalDimensions
        )

    imp = Importer(id_resolver)
    stencils = imp.Import_Stencils(stencilInstantiation.internalIR.stencils)


    AccountForIJMap(stencils)
    AccountForKMap(stencils)
    RemoveUnusedDimensions(id_resolver, stencils)
    UnparseCode(stencils)
    RenameVariables(stencils, id_resolver)

    exp = Exporter(id_resolver, sdfg)

    for id in metadata.APIFieldIDs:
        name = id_resolver.GetName(id)
        shape = exp.GetShape(id)
        print("Add array: {} of size {}".format(name, shape))
        sdfg.add_array(name, shape, dtype=data_type)

    for id in metadata.temporaryFieldIDs:
        name = id_resolver.GetName(id)
        shape = exp.GetShape(id)
        print("Add transient: {} of size {}".format(name, shape))
        sdfg.add_transient(name, shape, dtype=data_type)

    for id in metadata.globalVariableIDs:
        name = id_resolver.GetName(id)
        print("Add scalar: {}".format(name))
        sdfg.add_scalar(name, data_type)

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

    
