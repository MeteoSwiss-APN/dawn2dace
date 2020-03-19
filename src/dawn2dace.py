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

def filter_by_second(first, second):
    return tuple(f for f, s in zip(first, second) if s)

I = dace.symbol("I")
J = dace.symbol("J")
K = dace.symbol("K")
halo = dace.symbol("halo")

class KeywordReplacer_IIR(IIR_Transformer):
    def __init__(self):
        self.reserved_keywords = {
            "False", "class", "finally", "is", "return", "None", "continue", "for", 
            "lambda", "try", "True", "def", "from", "nonlocal", "while", "and", "del", 
            "global", "not", "with", "as", "elif", "if", "or", "yield", "assert", "else", 
            "import", "pass", "break", "except", "in", "raise", "x", "y", "z"}
    def visit_VarAccessExpr(self, expr):
        if expr.name in self.reserved_keywords:
            expr.name += '_'
        return expr
    def visit_FieldAccessExpr(self, expr):
        if expr.name in self.reserved_keywords:
            expr.name += '_'
        return expr

class KeywordReplacer_D2D(D2D_Transformer):
    def visit_Statement(self, stmt):
        stmt.code = KeywordReplacer_IIR().visit(stmt.code)
        return stmt

def ReplaceKeywords(stencils: list):
    """ Replaces reserved python keywords by appending an _."""
    KeywordReplacer_D2D().visit(stencils)



# TODO: Refactor this so it's a python AST transformer
class AssignmentExpander_IIR(IIR_Transformer):
    """ Makes dataflow more explicit by expanding 'a (op)= b' into 'a = a (op) b'. """
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

class AssignmentExpander_D2D(D2D_Transformer):
    def visit_Statement(self, stmt):
        stmt.code = AssignmentExpander_IIR().visit(stmt.code)
        return stmt

def ExpandAssignmentOperator(stencils: list):
    AssignmentExpander_D2D().visit(stencils)



class CodeUnparser(D2D_Transformer):
    def __init__(self, id_resolver:IdResolver):
        self.id_resolver = id_resolver
    def visit_Statement(self, stmt):
        stmt.code = Unparser(self.id_resolver).unparse_body_stmt(stmt.code)
        print(stmt.code)
        return stmt

def UnparseCode(stencils: list, id_resolver:IdResolver):
    """ Unparses C++ AST to Python string. """
    CodeUnparser(id_resolver).visit(stencils)



class Renamer_PyAST(ast.NodeTransformer):
    def __init__(self):
        self.storemode = False

    def visit_Name(self, node):
        if node.id == "true" or node.id == "false" or node.id == "True" or node.id == "False":
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

class Renamer_D2D(D2D_Transformer):
    def visit_Statement(self, stmt):
        tree = ast.parse(stmt.code)
        stmt.code = astunparse.unparse(Renamer_PyAST().visit(tree))
        print(stmt.code)
        return stmt

def RenameVariables(stencils: list):
    """ Adds a suffixes '_in'/'_out' to all variables that are read/write-accessed. """
    Renamer_D2D().visit(stencils)


# class K_Offsetter(IIR_Transformer):
#     """ Ofsets the k-index by a given value per id. """
#     def __init__(self, k_offsets:dict):
#         self.k_offsets = k_offsets # dict[id, int]

#     def visit_FieldAccessExpr(self, expr):
#         id = expr.data.accessID.value
#         expr.vertical_offset += self.k_offsets.get(id, 0) # offsets by 0 if not in dict.
#         return expr

# def AccountForKMapMemlets(stencils: list, id_resolver):
#     """
#     For every parallel multi-stage we introduce a k-map.
#     Thus the k-accesses need to be offsetted.
#     """
#     for stencil in stencils:
#         for multi_stage in stencil.multi_stages:
#             if multi_stage.execution_order == 2: # parallel
#                 multi_stage.SaveSpans()
#                 for stage in multi_stage.stages:
#                     for do_method in stage.do_methods:
#                         for stmt in do_method.statements:
#                             # Taking care of the reads.
#                             k_read_offset_dict = { # a dict{id:k_offset} where k_offset states how much an access to a variable needs to be offsetted.
#                                 id: -mem_acc.k.lower 
#                                 for id, mem_acc in multi_stage.unoffsetted_read_spans.items() 
#                                 if id in stmt.reads and not id_resolver.IsLocal(id) # locals don't need offsetting
#                                 }
#                             stmt.code = K_Offsetter(k_read_offset_dict).visit(stmt.code) # Offsetting the code.

#                             # Offsetting the AST.
#                             for id, offset in k_read_offset_dict.items():
#                                 stmt.reads[id].offset(k = offset)


#                             # Taking care of the writes.
#                             k_write_offset_dict = { 
#                                 id: -mem_acc.k.lower
#                                 for id, mem_acc in multi_stage.unoffsetted_write_spans.items()
#                                 if id in stmt.writes and not id_resolver.IsLocal(id) # locals don't need offsetting
#                                 }
#                             stmt.code = K_Offsetter(k_write_offset_dict).visit(stmt.code) # Offsetting the code.

#                             # Offsetting the AST.
#                             for id, offset in k_write_offset_dict.items():
#                                 stmt.writes[id].offset(k = offset)


# def AccountForIJMapMemlets(stencils: list):
#     """ Offsets the k-index that each tasklet accesses [0,*]. """
#     for stencil in stencils:
#         for multi_stage in stencil.multi_stages:
#             for stage in multi_stage.stages:
#                 for do_method in stage.do_methods:
#                     for stmt in do_method.statements:
#                         stmt.SaveSpans()

#                         # Taking care of the reads.
#                         k_read_offset_dict = { id: -mem_acc.k.lower for id, mem_acc in stmt.unoffsetted_read_spans.items() if id in stmt.reads }
#                         stmt.code = K_Offsetter(k_read_offset_dict).visit(stmt.code) # Offsetting the code.

#                         # Taking care of the writes.
#                         k_write_offset_dict = { id: -mem_acc.k.lower for id, mem_acc in stmt.unoffsetted_write_spans.items() if id in stmt.writes }
#                         stmt.code = K_Offsetter(k_write_offset_dict).visit(stmt.code) # Offsetting the code.

class K_Interval_Collector(D2D_Visitor):
    def __init__(self):
        self.intervals = []
    def visit_K_Interval(self, k_interval):
        self.intervals.append(k_interval)

def Collect_K_Intervals(ms:MultiStage):
    collector = K_Interval_Collector()
    collector.visit(ms)
    return collector.intervals

class Statement_Collector(D2D_Visitor):
    def __init__(self, correct:K_Interval):
        self.correct = correct
        self.statements = []
    def visit_DoMethod(self, do_method):
        if do_method.k_interval == self.correct:
            self.statements.extend(do_method.statements)

def CollectStatements(interval:K_Interval, ms:MultiStage):
    collector = Statement_Collector(interval)
    collector.visit(ms)
    return collector.statements

class K_Interval_Grouper(D2D_Transformer):
    def visit_MultiStage(self, ms):
        intervals = list(set(Collect_K_Intervals(ms)))
        intervals.sort(
            key = lambda intervals: intervals.begin_as_value(K = 1000),
            reverse = (ms.execution_order == ExecutionOrder.Backward_Loop)
        )
        ms.k_sections = [K_Section(iv, CollectStatements(iv, ms)) for iv in intervals]
        ms.stages = []
        return ms

def Group_by_K_Intervals(stencils: list):
    """ Replaces Stages and DoMethods with K_Sections. """
    K_Interval_Grouper().visit(stencils)


# def Group_by_K_Intervals(stencils: list):
#     """ Replaces Stages and DoMethods with K_Sections. """
#     for stencil in stencils:
#         for multi_stage in stencil.multi_stages:
#             intervals = set()
#             for stage in multi_stage.stages:
#                 for do_method in stage.do_methods:
#                     intervals.add(do_method.k_interval)
#             intervals = list(intervals)
            
#             intervals.sort(
#                 key = lambda intervals: intervals.begin_as_value(K = 1000),
#                 reverse = (multi_stage.execution_order == ExecutionOrder.Backward_Loop)
#             )

#             for interval in intervals:
#                 statements = []
#                 for stage in multi_stage.stages:
#                     for do_method in stage.do_methods:
#                         if do_method.k_interval == interval:
#                             for stmt in do_method.statements:
#                                 statements.append(stmt)
#                 multi_stage.k_sections.append(K_Section(interval, statements))

#             multi_stage.stages = []


def ReplaceMultiStages(stencils: list):
    """ Replaces MultiStages with Maps or Loops. """
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for section in multi_stage.k_sections:
                if multi_stage.execution_order == ExecutionOrder.Parallel.value:
                    stencil.map_or_loops.append(Map(section.interval, section.statements))
                else:
                    ascending = (multi_stage.execution_order == ExecutionOrder.Forward_Loop.value)
                    stencil.map_or_loops.append(Loop(section.interval, ascending, section.statements))

        stencil.multi_stages = []

def DimensionalMask(id:int, id_resolver:IdResolver) -> Bool3D:
    """ Returns a Bool3D where the bools state if the dimension is present in the corresponding array. """
    dims = id_resolver.GetDimensions(id)
    return Bool3D(dims.i != 0, dims.j != 0, dims.k != 0)

def TranslateTransactions(transactions:dict, id_resolver:IdResolver):
    ret = {}
    for id, mem_acc in transactions.items():
        name = self.id_resolver.GetName(id)
        if not self.id_resolver.IsALiteral(id):
            ret[name] = (DimensionalMask(id, id_resolver), mem_acc)
    return ret

def BoundaryConditions(transactions:dict, id_resolver:IdResolver):
    ret = {}
    for id, mem_acc in transactions.items():
        name = self.id_resolver.GetName(id)
        if id_resolver.IsInAPI(id): # Workaround for missing shape inferance information in IIR.
            h = RelMemAcc3D(RelMemAcc1D(halo, halo), RelMemAcc1D(halo, halo), RelMemAcc1D(0, 0))
        else:
            h = mem_acc
        ret[name] = { "btype": "shrink", "halo": h }
    return ret

def IntroduceStencilNode(stencils: list, id_resolver:IdResolver):
    """ Replaces Statements with StencilNode. """
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for map_or_loop in multi_stage.map_or_loops:
                for stmt in map_or_loop.statements:
                    stencil_node = StencilNode(
                        stmt.line,
                        stmt.code,
                        Int3D(I, J, 1),
                        TranslateTransactions(stmt.reads, id_resolver),
                        TranslateTransactions(stmt.writes, id_resolver),
                        BoundaryConditions(stmt.writes, id_resolver)
                    )
                    map_or_loop.stencil_nodes.append(stencil_node)
    

class MemLayoutTransformer(ast.NodeTransformer):
    def visit_Subscript(self, node):
        if isinstance(node.slice.value, ast.Tuple): # multi-dimensional access
            elts = Any3D(node.slice.value.elts[0], node.slice.value.elts[1], node.slice.value.elts[2])
            elts = ToMemLayout(elts)
            node.slice.value.elts[0], node.slice.value.elts[1], node.slice.value.elts[2] = elts.i, elts.j, elts.k
        else:
            raise Exception('Wrong type!')
        return node

def AdaptToMemoryLayout(id_resolver:IdResolver, stencils: list):
    for stencil in stencils:
        for map_or_loop in stencil.map_or_loops:
            for sn in map_or_loop.stencil_nodes:
                print("Memory untransformed: " + sn.code)
                tree = ast.parse(sn.code)
                sn.code = astunparse.unparse(MemLayoutTransformer().visit(tree))
                print("Memory transformed: " + sn.code)
                sn.shape = ToMemLayout(sn.shape)
                sn.reads = { k : (ToMemLayout(v[0]), ToMemLayout(v[1])) for k,v in sn.reads.items() }
                sn.writes = { k : (ToMemLayout(v[0]), ToMemLayout(v[1])) for k,v in sn.writes.items() }
                sn.boundary_conditions = { k : { kk : (vv if kk != 'halo' else ToMemLayout(vv)) for kk,vv, in v } for k,v in sn.boundary_conditions }

class DimensionalReducer(IIR_Transformer):
    def __init__(self, id_resolver:IdResolver, transfer:dict):
        self.id_resolver = id_resolver
        self.transfer = transfer

    def visit_FieldAccessExpr(self, expr):
        id = expr.data.accessID.value
        if id in self.transfer:
            dims = self.id_resolver.GetDimensions(id)

            if not dims.i:
                expr.cartesian_offset.i_offset = -1000
            if not dims.j:
                expr.cartesian_offset.j_offset = -1000
            if not dims.k:
                 expr.vertical_offset = -1000
        return expr

class DimensionalReducerRead(DimensionalReducer):
    def __init__(self, id_resolver:IdResolver, reads:dict):
        super().__init__(id_resolver, reads)

    def visit_AssignmentExpr(self, expr):
        expr.right.CopyFrom(self.visit(expr.right))
        return expr

class DimensionalReducerWrite(DimensionalReducer):
    def __init__(self, id_resolver:IdResolver, writes:dict):
        super().__init__(id_resolver, writes)

    def visit_AssignmentExpr(self, expr):
        expr.left.CopyFrom(self.visit(expr.left))
        return expr

def MarkUnusedDimensions(id_resolver:IdResolver, stencils: list):
    """ Marks all unused dimensions in all field access expressions. """
    for stencil in stencils:
        for map_or_loop in stencil.map_or_loops:
            for stencil_node in map_or_loop.stencil_nodes:
                stencil_node.code = DimensionalReducerRead(id_resolver, stencil_node.reads).visit(stencil_node.code)
                stencil_node.code = DimensionalReducerWrite(id_resolver, stencil_node.writes).visit(stencil_node.code)

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

    # Code preprocessing
    ReplaceKeywords(stencils) # Prevents name collisions. 'in' -> 'in_'
    ExpandAssignmentOperator(stencils) # Makes data flow explicit. 'a += b' -> 'a = a + b'
    UnparseCode(stencils, id_resolver) # C++ AST -> Python string
    RenameVariables(stencils) # 'a = a' -> 'a_out = a_in'

    # TODO: Find out what they do
    # AccountForKMapMemlets(stencils, id_resolver)
    # AccountForIJMapMemlets(stencils)

    # Tree transformations
    Group_by_K_Intervals(stencils) # Sorts control flow. (Stages x DoMethods) -> K_Sections
    ReplaceMultiStages(stencils) # MultiStages -> (Map, Loop)
    IntroduceStencilNode(stencils, id_resolver) # Statements -> StencilNode

    AdaptToMemoryLayout(id_resolver, stencils)
    MarkUnusedDimensions(id_resolver, stencils)

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

    
