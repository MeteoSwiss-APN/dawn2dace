import dace
import argparse
import ast
import os
import pickle
import sys
import astunparse
import IIR_pb2
from IndexHandling import *
from Intermediates import *
from Importer import Importer
from Exporter import Exporter
from IdResolver import IdResolver
from Unparser import Unparser
from IIR_AST import *

RESERVED_PYTHON_KEYWORDS = {"False", "class", "finally", "is", "return", "None", "continue", "for", "lambda", "try", "True", "def", "from", "nonlocal", "while", "and", "del", "global", "not", "with", "as", "elif", "if", "or", "yield", "assert", "else", "import", "pass", "break", "except", "in", "raise"}

class KeywordReplacer(IIR_Transformer):
    def visit_VarAccessExpr(self, expr):
        if expr.name in RESERVED_PYTHON_KEYWORDS:
            expr.name += '_'
        return expr

    def visit_FieldAccessExpr(self, expr):
        if expr.name in RESERVED_PYTHON_KEYWORDS:
            expr.name += '_'
        return expr

def ReplaceKeywords(stencils: list):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        stmt.code = KeywordReplacer().visit(stmt.code)

class InOut_Renamer(ast.NodeTransformer):
    def __init__(self):
        self.storemode = False

    def visit_Name(self, node):
        if node.id == "true":
            return node
        if node.id == "false":
            return node
        if node.id.startswith('__local'):
            return node

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

    def visit_Call(self, node):
        for arg in node.args:
            self.visit(arg)
        return node

def RenameVariables_InOut(stencils: list):
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
                        stmt.code = astunparse.unparse(InOut_Renamer().visit(tree))
                        print(stmt.code)


class AssignmentExpander(IIR_Transformer):
    """ Makes dataflow explicit by expanding 'a (op)= b' into 'a = a (op) b'. """
    def visit_AssignmentExpr(self, expr):
        if expr.op == '=':
            return expr
        
        novum = IIR_pb2.SIR_dot_statements__pb2.BinaryOperator()
        novum.left.CopyFrom(expr.left)
        novum.op = expr.op[0]
        novum.right.CopyFrom(expr.right)

        expr.right.Clear()
        expr.op = '='
        expr.right.binary_operator.CopyFrom(novum)
        return expr

def ExpandAssignmentOperator(stencils: list):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        stmt.code = AssignmentExpander().visit(stmt.code)


# class IJ_Mapper(IIR_Transformer):
#     """ Offsets the i and j-index when there's a span. """
#     def __init__(self, transfer:dict):
#         self.transfer = transfer

#     def visit_FieldAccessExpr(self, expr):
#         id = expr.data.accessID.value
#         if id in self.transfer:
#             mem_acc = self.transfer[id]
#             if mem_acc.i.lower != mem_acc.i.upper:
#                 expr.cartesian_offset.i_offset -= mem_acc.i.lower
#             if mem_acc.j.lower != mem_acc.j.upper:
#                 expr.cartesian_offset.j_offset -= mem_acc.j.lower
#         return expr

# def AccountForIJMap(stencils: list):
#     """ Offsets the i and j-index when there's a span. """
#     for stencil in stencils:
#         for multi_stage in stencil.multi_stages:
#             for stage in multi_stage.stages:
#                 for do_method in stage.do_methods:
#                     for stmt in do_method.statements:
#                         stmt.code = IJ_Mapper(stmt.Reads()).visit(stmt.code)

def SplitMultiStages(stencils: list):
    for stencil in stencils:
        new_ms = []
        for multi_stage in stencil.multi_stages:
            intervals = list(set(do_method.k_interval
                for stage in multi_stage.stages
                for do_method in stage.do_methods
                ))
            intervals.sort(
                key = lambda interval: FullEval(interval.lower, 'K', 1000),
                reverse = (multi_stage.execution_order == ExecutionOrder.Backward_Loop)
            )
            for interval in intervals:
                new_stages = []
                for stage in multi_stage.stages:
                    new_stages.append(Stage([dm for dm in stage.do_methods if dm.k_interval == interval], stage.extents))
                new_ms.append(MultiStage(multi_stage.execution_order, new_stages))
        stencil.multi_stages = new_ms



def AddMsMemlets(stencils: list, id_resolver):
    """
    For every parallel multi-stage we introduce a k-map.
    Thus the k-accesses need to be offsetted.
    """
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            if multi_stage.execution_order == ExecutionOrder.Parallel.value:
                # defines the slices of memory that will be mapped inside this multistage's scope.
                multi_stage.read_memlets = copy.deepcopy(multi_stage.Reads())
                multi_stage.write_memlets = copy.deepcopy(multi_stage.Writes())

                for stage in multi_stage.stages:
                    for do_method in stage.do_methods:
                        for stmt in do_method.statements:
                            k_read_offsets = { id: -acc.k.lower for id, acc in multi_stage.read_memlets.items() if id in stmt.ReadIds() }
                            stmt.offset_reads(k_read_offsets)

                            k_write_offsets = { id: -acc.k.lower for id, acc in multi_stage.write_memlets.items() if id in stmt.WriteIds() }
                            stmt.offset_writes(k_write_offsets)


def AddStencilMemlets(stencils: list):
    """ Offsets the k-index that each stencil accesses. """
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    do_method.read_memlets = copy.deepcopy(do_method.Reads())
                    do_method.write_memlets = copy.deepcopy(do_method.Writes())

                    for stmt in do_method.statements:
                        k_read_offsets = { id: -acc.k.lower for id, acc in do_method.read_memlets.items() if id in stmt.ReadIds() }
                        stmt.offset_reads(k_read_offsets)

                        k_write_offsets = { id: -acc.k.lower for id, acc in do_method.write_memlets.items() if id in stmt.WriteIds() }
                        stmt.offset_writes(k_write_offsets)


class DimensionalReducer(IIR_Transformer):
    def __init__(self, id_resolver:IdResolver, transfer:set):
        self.id_resolver = id_resolver
        self.transfer = transfer

    def visit_FieldAccessExpr(self, expr):
        id = expr.data.accessID.value
        if id in self.transfer:
            name = self.id_resolver.GetName(id)
            dims = self.id_resolver.GetDimensions(id)

            if not dims.i:
                expr.cartesian_offset.i_offset = -1000
            if not dims.j:
                expr.cartesian_offset.j_offset = -1000
            if not dims.k:
                 expr.vertical_offset = -1000
        return expr

class DimensionalReducerRead(DimensionalReducer):
    def __init__(self, id_resolver:IdResolver, reads:set):
        super().__init__(id_resolver, reads)

    def visit_AssignmentExpr(self, expr):
        expr.right.CopyFrom(self.visit(expr.right))
        return expr

class DimensionalReducerWrite(DimensionalReducer):
    def __init__(self, id_resolver:IdResolver, writes:set):
        super().__init__(id_resolver, writes)

    def visit_AssignmentExpr(self, expr):
        expr.left.CopyFrom(self.visit(expr.left))
        return expr

def RemoveUnusedDimensions(id_resolver:IdResolver, stencils: list):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        stmt.code = DimensionalReducerRead(id_resolver, stmt.ReadIds()).visit(stmt.code)
                        stmt.code = DimensionalReducerWrite(id_resolver, stmt.WriteIds()).visit(stmt.code)


def UnparseCode(stencils: list, id_resolver:IdResolver):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        stmt.code = Unparser(id_resolver).unparse_body_stmt(stmt.code)
                        print("code: " + stmt.code)

def IIR_str_to_SDFG(iir: str):
    stencilInstantiation = IIR_pb2.StencilInstantiation()
    stencilInstantiation.ParseFromString(iir)

    metadata = stencilInstantiation.metadata
    id_resolver = IdResolver(
        metadata.accessIDToName,
        metadata.APIFieldIDs,
        metadata.temporaryFieldIDs,
        metadata.globalVariableIDs,
        metadata.fieldIDtoDimensions
        )

    sdfg = dace.SDFG(metadata.stencilName)

    imp = Importer(id_resolver)
    stencils = imp.Import_Stencils(stencilInstantiation.internalIR.stencils)

    ReplaceKeywords(stencils)
    ExpandAssignmentOperator(stencils)
    SplitMultiStages(stencils)
    AddMsMemlets(stencils, id_resolver)
    AddStencilMemlets(stencils)
    #AccountForIJMap(stencils)
    RemoveUnusedDimensions(id_resolver, stencils)
    UnparseCode(stencils, id_resolver)
    RenameVariables_InOut(stencils)

    exp = Exporter(id_resolver, sdfg)

    exp.try_add_array(sdfg, metadata.APIFieldIDs)
    exp.try_add_transient(sdfg, metadata.temporaryFieldIDs)
    
    exp.Export_Globals({ id : stencilInstantiation.internalIR.globalVariableToValue[id_resolver.GetName(id)].value for id in metadata.globalVariableIDs })
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

    
