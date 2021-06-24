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
from Exporter import Exporter
from IdResolver import IdResolver
from Unparser import Unparser
from IIR_AST import *

def UnparseCode(stencils: list, id_resolver:IdResolver):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    for stmt in do_method.statements:
                        stmt.code = Unparser(id_resolver).unparse_body_stmt(stmt.code)
                        print(stmt.code)

class ReplaceSubscript(ast.NodeTransformer):
    " Replaces subscript with name"

    def __init__(self, repldict):
        "repldict: Dict[(variable_name, index), new_name]"
        self.replace = repldict

    def visit_Subscript(self, node: ast.Subscript):
        name = node.value.id
        if isinstance(node.slice.value, ast.Constant):
            index = (node.slice.value.value,)
        elif isinstance(node.slice.value, ast.UnaryOp):
            index = (-node.slice.value.operand.value,)
        else:
            index = tuple((-elt.operand.value if isinstance(elt, ast.UnaryOp) else elt.value) for elt in node.slice.value.elts)
        key = (name, index)
        if isinstance(node.value, ast.Name) and (key in self.replace):
            return ast.copy_location(ast.Name(id=self.replace[key]), node)
        return self.generic_visit(node)

def AddRegisters(stencils: list, id_resolver):
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:

                    writes = {}
                    reads = {}
                    for stmt in do_method.statements:
                        reads = FuseIntervalDicts([reads, Subtract(stmt.Reads(), writes)])
                        writes = FuseIntervalDicts([writes, stmt.Writes()])

                    # Construct replace dictionary, in-code and out-code
                    replace_dict = {} # Dict[(variable_name, index), new_name]

                    in_code = "" # Reads memory into registers
                    for id, interval in reads.items():
                        if id_resolver.IsLocal(id):
                            continue
                        name = id_resolver.GetName(id)
                        for index in interval.range():
                            reduced_index = id_resolver.DimFilterIndex(id, index)
                            new_name = f'{name}_{len(replace_dict)}'
                            replace_dict[(name, reduced_index)] = new_name
                            in_code += f"{new_name} = {name}_in[{reduced_index}]\n"

                    out_code = "" # Writes registers into memory
                    for id, interval in writes.items():
                        if id_resolver.IsLocal(id):
                            continue
                        name = id_resolver.GetName(id)
                        for index in interval.range():
                            reduced_index = id_resolver.DimFilterIndex(id, index)
                            if (name, reduced_index) in replace_dict:
                                new_name = replace_dict[(name, reduced_index)]
                            else:
                                new_name = f'{name}_{len(replace_dict)}'
                                replace_dict[(name, reduced_index)] = new_name
                            out_code += f"{name}_out[{reduced_index}] = {new_name}\n"

                    in_stmt = Statement(in_code, line=0, reads=reads, writes={})
                    out_stmt = Statement(out_code, line=0, reads={}, writes=writes)

                    # Transform Statements
                    for stmt in do_method.statements:
                        tree = ast.parse(stmt.code)
                        stmt.code = astunparse.unparse(ReplaceSubscript(replace_dict).visit(tree))
                        stmt.reads = {}
                        stmt.writes = {}
                    
                    do_method.statements.insert(0, in_stmt)
                    do_method.statements.append(out_stmt)


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
                reverse = (multi_stage.execution_order == ExecutionOrder.Backward_Loop.value)
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
                            stmt.OffsetReads(k_read_offsets, id_resolver)

                            k_write_offsets = { id: -acc.k.lower for id, acc in multi_stage.write_memlets.items() if id in stmt.WriteIds() }
                            stmt.OffsetWrites(k_write_offsets, id_resolver)


def AddDoMethodMemlets(stencils: list, id_resolver):
    """ Offsets the k-index that each DoMethod accesses. """
    for stencil in stencils:
        for multi_stage in stencil.multi_stages:
            for stage in multi_stage.stages:
                for do_method in stage.do_methods:
                    do_method.read_memlets = copy.deepcopy(do_method.Reads())
                    do_method.write_memlets = copy.deepcopy(do_method.Writes())

                    for stmt in do_method.statements:
                        k_read_offsets = { id: -acc.k.lower for id, acc in do_method.read_memlets.items() if id in stmt.ReadIds() }
                        stmt.OffsetReads(k_read_offsets, id_resolver)

                        k_write_offsets = { id: -acc.k.lower for id, acc in do_method.write_memlets.items() if id in stmt.WriteIds() }
                        stmt.OffsetWrites(k_write_offsets, id_resolver)

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

    imp = Importer(id_resolver)
    stencils = imp.Import_Stencils(stencilInstantiation.internalIR.stencils)

    UnparseCode(stencils, id_resolver)
    AddRegisters(stencils, id_resolver)
    SplitMultiStages(stencils)
    AddMsMemlets(stencils, id_resolver)
    AddDoMethodMemlets(stencils, id_resolver)
    
    exp = Exporter(id_resolver, name=metadata.stencilName)
    exp.Export_ApiFields(metadata.APIFieldIDs)
    exp.Export_TemporaryFields(metadata.temporaryFieldIDs)    
    exp.Export_Globals({ id : stencilInstantiation.internalIR.globalVariableToValue[id_resolver.GetName(id)].value for id in metadata.globalVariableIDs })
    exp.Export_Stencils(stencils)

    exp.sdfg.fill_scope_connectors()
    return exp.sdfg

def IIR_file_to_SDFG_file(iir_file: str, sdfg_file: str):
    with open(iir_file) as f:
        iir = f.read()

    sdfg = IIR_str_to_SDFG(iir)

    sdfg.save(sdfg_file, use_pickle=False)
   
