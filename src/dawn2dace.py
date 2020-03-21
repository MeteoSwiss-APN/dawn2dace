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
from IdResolver import *
from Unparser import Unparser
from IIR_AST import *
from stencilflow.stencil.stencil import Stencil as StencilLib
import itertools

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def try_add_array(sdfg, id_resolver:IdResolver, ids:list):
    for id in ids:
        name = id_resolver.GetName(id)
        shape = id_resolver.GetShape(id)
        strides = id_resolver.GetStrides(id)
        total_size = id_resolver.GetTotalSize(id)
        if __debug__:
            print("Try add array: {} of size {} with strides {} and total size {}".format(name, shape, strides, total_size))
        try:
            sdfg.add_array(
                name, 
                shape,
                dtype=data_type,
                strides=strides, 
                total_size=total_size
            )
        except:
            pass

def try_add_transient(sdfg, id_resolver:IdResolver, ids:list):
    for id in ids:
        name = id_resolver.GetName(id)
        shape = id_resolver.GetShape(id)
        strides = id_resolver.GetStrides(id)
        total_size = id_resolver.GetTotalSize(id)
        if __debug__:
            print("Try add transient: {} of size {} with strides {} and total size {}".format(name, shape, strides, total_size))
        try:
            sdfg.add_transient(
                name, 
                shape,
                dtype=data_type,
                strides=strides, 
                total_size=total_size
            )
        except:
            pass

def try_add_scalar(sdfg, id_resolver:IdResolver, ids:list):    
    for id in ids:
        name = id_resolver.GetName(id)
        if __debug__:
            print("Try add scalar: {}".format(name))
        try:
            sdfg.add_scalar(name, dtype=data_type)
        except:
            pass


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


class MultiStageReplacer(D2D_Transformer):
    def visit_Stencil(self, stencil):
        for ms in stencil.multi_stages:
            for section in ms.k_sections:
                if ms.execution_order == ExecutionOrder.Parallel.value:
                    stencil.control_flow.append(Map(section.interval, section.statements))
                else:
                    ascending = (ms.execution_order == ExecutionOrder.Forward_Loop.value)
                    stencil.control_flow.append(Loop(section.interval, ascending, section.statements))
        stencil.multi_stages = []
        return stencil

def ReplaceMultiStages(stencils: list):
    """ Replaces MultiStages with Maps or Loops. """
    MultiStageReplacer().visit(stencils)


class StencilNodeIntroducer(D2D_Transformer):
    def __init__(self, id_resolver:IdResolver):
        self.id_resolver = id_resolver

    def DimensionalMask(self, id:int) -> Bool3D:
        """ Returns a Bool3D where the bools state if the dimension is present in the corresponding array. """
        dims = self.id_resolver.GetDimensions(id)
        return Bool3D(dims.i != 0, dims.j != 0, dims.k != 0)

    def TranslateTransactions(self, transactions:dict):
        ret = {}
        for id, mem_acc in transactions.items():
            if not self.id_resolver.IsALiteral(id):
                ret[id] = (self.DimensionalMask(id), mem_acc)
        return ret

    def BoundaryConditions(self, transactions:dict):
        ret = {}
        for id, mem_acc in transactions.items():
            if self.id_resolver.IsInAPI(id): # Workaround for missing shape inferance information in IIR.
                h = RelMemAcc3D(RelMemAcc1D(halo, halo), RelMemAcc1D(halo, halo), RelMemAcc1D(0, 0))
            else:
                h = mem_acc
            ret[id] = h
        return ret

    def visit_Map(self, m):
        m.stencil_nodes = [
            StencilNode(
                stmt.line,
                stmt.code,
                Int3D(I, J, 1), # k==1 because it's in a k-loop.
                self.TranslateTransactions(stmt.reads),
                self.TranslateTransactions(stmt.writes),
                self.BoundaryConditions(stmt.writes)
            ) for stmt in m.statements
        ]
        m.statements = []
        return m

    def visit_Loop(self, loop):
        loop.stencil_nodes = [
            StencilNode(
                stmt.line,
                stmt.code,
                Int3D(I, J, 1), # k==1 because it's in a k-loop.
                self.TranslateTransactions(stmt.reads),
                self.TranslateTransactions(stmt.writes),
                self.BoundaryConditions(stmt.writes)
            ) for stmt in loop.statements
        ]
        loop.statements = []
        return loop

def IntroduceStencilNode(stencils: list, id_resolver:IdResolver):
    """ Replaces Statements with StencilNode. """
    StencilNodeIntroducer(id_resolver).visit(stencils)
    
    

class MemLayoutTransformer_PyAST(ast.NodeTransformer):
    def visit_Subscript(self, node):
        if isinstance(node.slice.value, ast.Tuple): # multi-dimensional access
            elts = Any3D(node.slice.value.elts[0], node.slice.value.elts[1], node.slice.value.elts[2])
            elts = ToMemLayout(elts)
            node.slice.value.elts[0], node.slice.value.elts[1], node.slice.value.elts[2] = elts.i, elts.j, elts.k
        else:
            raise Exception('Wrong type!')
        return node

class MemLayoutTransformer_D2D(D2D_Transformer):
    def visit_StencilNode(self, sn):
        print("Memory untransformed: " + sn.code)
        tree = ast.parse(sn.code)
        sn.code = astunparse.unparse(MemLayoutTransformer_PyAST().visit(tree))
        print("Memory transformed: " + sn.code)
        sn.shape = ToMemLayout(sn.shape)
        sn.reads = { k : (ToMemLayout(v[0]), ToMemLayout(v[1])) for k,v in sn.reads.items() }
        sn.writes = { k : (ToMemLayout(v[0]), ToMemLayout(v[1])) for k,v in sn.writes.items() }
        sn.bcs = { k:ToMemLayout(v) for k,v in sn.bcs.items() }
        return sn

def AdaptToMemoryLayout(stencils: list):
    MemLayoutTransformer_D2D().visit(stencils)



class DimensionalFilter_PyAST(ast.NodeTransformer):
    def __init__(self, transfers:dict):
        self.transfers = transfers
    def visit_Subscript(self, node):
        name = node.value.id
        if isinstance(node.slice.value, ast.Tuple): # multi-dimensional access
            accesses_dimension = self.transfers[name][0]
            node.slice.value.elts = filter_by_second(node.slice.value.elts, accesses_dimension)
        else:
            raise Exception('Wrong type!')
        return node

class DimensionalFilter_D2D(D2D_Transformer):
    def __init__(self, id_resolver:IdResolver):
        self.id_resolver = id_resolver
    def visit_StencilNode(self, sn):
        print("Dimensions unfiltered: " + sn.code)
        tree = ast.parse(sn.code)
        reads_with_suffix = { self.id_resolver.GetName(k)+'_in':v for k,v in sn.reads.items() }
        writes_with_suffix = { self.id_resolver.GetName(k)+'_out':v for k,v in sn.reads.items() }
        merged_transactions_with_suffix = {**reads_with_suffix , **writes_with_suffix}
        sn.code = astunparse.unparse(DimensionalFilter_PyAST(merged_transactions_with_suffix).visit(tree))
        print("Dimensions filtered: " + sn.code)
        return sn

def RemoveUnusedDimensions(stencils: list, id_resolver:IdResolver):
    """ Removes all unused dimensions in all code field access expressions. """
    DimensionalFilter_D2D(id_resolver).visit(stencils)



def AddGlobalInit(sdfg, id_resolver:IdResolver, values:dict): # returns the dace state or None.
    try_add_scalar(sdfg, id_resolver, values.keys())

    state = sdfg.add_state("GlobalInit")
    for id, value in values.items():
        name = self.id_resolver.GetName(id)
        sdfg.add_scalar(name, dtype=data_type, transient=True)
        tasklet = state.add_tasklet(name,
            inputs=None,
            outputs={name},
            code="{} = {}".format(name, value)
        )
        out_memlet = dace.Memlet.simple(name, subset_str = '0')
        state.add_edge(tasklet, name, state.add_write(name), None, out_memlet)
    return state

def DaisyChainStates(states:list, sdfg):
    """ Daisy chains the states. The states have to be in the sdfg. """
    for a, b in pairwise(states):
        sdfg.add_edge(a, b, dace.InterstateEdge())

class ControlFlowAdder(D2D_Transformer):
    def __init__(self, sdfg, last_state, id_resolver:IdResolver):
        self.sdfg = sdfg # The current context
        self.last_state = last_state
        self.id_resolver = id_resolver

    def visit_Map(self, m):
        # Sets up control flow.
        m.state = self.sdfg.add_state("state_{}".format(CreateUID()))
        m.sdfg = dace.SDFG("ms_subsdfg{}".format(CreateUID()))
        m.nested_sdfg = m.state.add_nested_sdfg(
            m.sdfg, 
            self.sdfg,
            set(self.id_resolver.GetName(id) for id in m.ReadKeys),
            set(self.id_resolver.GetName(id) for id in m.WriteKeys),
        )
        m.map_entry, m.map_exit = m.state.add_map("kmap", dict(k=str(m.interval)))

        if self.last_state is not None:
            DaisyChainStates([self.last_state, m.state], self.sdfg)
        self.last_state = m.state

        return m

    def visit_Loop(self, loop):
        loop.first_state = self.sdfg.add_state("dummy_{}".format(CreateUID()))
        loop.last_state = self.sdfg.add_state("dummy_{}".format(CreateUID()))

        if loop.ascending:
            initialize_expr = loop.interval.begin_as_str()
            condition_expr = "k < {}".format(loop.interval.end_as_str())
            increment_expr = "k + 1"
        else:
            initialize_expr = loop.interval.end_as_str(offset = -1)
            condition_expr = "k >= {}".format(loop.interval.begin_as_str())
            increment_expr = "k - 1"

        _, _, self.last_state = self.sdfg.add_loop(
            before_state = self.last_state,
            loop_state = loop.first_state,
            loop_end_state = loop.last_state,
            after_state = None,
            loop_var = "k",
            initialize_expr = initialize_expr,
            condition_expr = condition_expr,
            increment_expr = increment_expr
        )
        return loop


def AddControlFlow(stencils: list, sdfg, last_state, id_resolver:IdResolver):
    ControlFlowAdder(sdfg, last_state, id_resolver).visit(stencils)



class MapDummyConnector(D2D_Visitor):
    def __init__(self, sdfg):
        self.sdfg = sdfg # The current context
    def visit_Map(self, m):
        m.state.add_edge(m.map_entry, None, m.nested_sdfg, None, dace.EmptyMemlet())
        m.state.add_edge(m.nested_sdfg, None, m.map_exit, None, dace.EmptyMemlet())
    def visit_Loop(self, loop):
        pass

def ConnectMapDummies(stencils: list, sdfg):
    MapDummyConnector(sdfg).visit(stencils)

class LoopDummyConnector(D2D_Visitor):
    def __init__(self, sdfg):
        self.sdfg = sdfg # The current context
    def visit_Map(self, m):
        pass
    def visit_Loop(self, loop):
        DaisyChainStates([loop.first_state, loop.last_state], self.sdfg)

def ConnectLoopDummies(stencils: list, sdfg):
    LoopDummyConnector(sdfg).visit(stencils)



class MapFiller(D2D_Visitor):
    def __init__(self, sdfg, id_resolver:IdResolver):
        self.sdfg = sdfg # The current context
        self.id_resolver = id_resolver

    def try_add_array(self, sdfg, ids:list):
        try_add_array(sdfg, self.id_resolver, ids)
    def try_add_transient(self, sdfg, ids:list):
        try_add_transient(sdfg, self.id_resolver, ids)
    def try_add_scalar(self, sdfg, ids:list):
        try_add_scalar(sdfg, self.id_resolver, ids)

    def ExpandMemAcc(self, dim_present:Bool3D, mem_acc:RelMemAcc3D):
        accs = [list(filter_by_second(Any3D(i,j,k), dim_present)) \
            for i in range(mem_acc.i.lower, mem_acc.i.upper + 1)
            for j in range(mem_acc.j.lower, mem_acc.j.upper + 1)
            for k in range(mem_acc.k.lower, mem_acc.k.upper + 1)]
        return (list(ToMemLayout(dim_present)), accs)

    def CreateStencilLib(self, sn:StencilNode):
        return StencilLib(
            label = "Line{}".format(CreateUID()), # TODO: Replace with sn.line
            shape = list(sn.shape),
            accesses = { self.id_resolver.GetName(id)+'_in':self.ExpandMemAcc(v[0], v[1]) for id, v in sn.reads.items() },
            output_fields = { self.id_resolver.GetName(id)+'_out':self.ExpandMemAcc(v[0], v[1]) for id, v in sn.writes.items() },
            boundary_conditions = { self.id_resolver.GetName(id)+'_out': {'btype':'shrink', 'halo':list(ToMemLayout(mem_acc))} for id,mem_acc in sn.bcs.items() },
            code = sn.code
        )

    def MemletSubset(self, dim_present:Bool3D, mem_acc:RelMemAcc3D):
        subset = ','.join(
            filter_by_second(
                Any3D("0:I","0:J", "{}:{}".format(mem_acc.k.lower, mem_acc.k.upper))
                , dim_present
            )
        )
        if subset:
            return subset
        return '0'

    def visit_Map(self, m):
        self.map_sdfg = m.sdfg

        for sn in m.stencil_nodes:
            self.visit(sn)

    def visit_Loop(self, loop):
        pass

    def visit_StencilNode(self, sn):
        reads = sn.ReadKeys
        writes = sn.WriteKeys
        all = reads | writes
        apis, temporaries, globals, literals, locals = self.id_resolver.Classify(all)

        self.try_add_scalar(self.map_sdfg, reads & globals)
        self.try_add_array(self.map_sdfg, all - locals - globals - literals)
        self.try_add_transient(self.sdfg, all - locals - globals - literals)
        self.try_add_transient(self.map_sdfg, locals)

        sn.state = self.map_sdfg.add_state("state_{}".format(CreateUID()))
        stencil = self.CreateStencilLib(sn)
        sn.state.add_node(stencil)

        # Add stencil-input memlet paths, from state.read to stencil.
        for id, v in sn.reads.items():
            dims_present = v[0]
            mem_acc = v[1]
            name = self.id_resolver.GetName(id)
            memlet_subset = self.MemletSubset(dims_present, mem_acc)

            read = sn.state.add_read(name)
            sn.state.add_memlet_path(
                read,
                stencil,
                memlet = dace.Memlet.simple(name, memlet_subset),
                dst_conn = name + '_in',
                propagate=True
            )

        # Add stencil-output memlet paths, from stencil to state.write.
        for id, v in sn.writes.items():
            dims_present = v[0]
            mem_acc = v[1]
            name = self.id_resolver.GetName(id)
            memlet_subset = self.MemletSubset(dims_present, mem_acc)

            write = sn.state.add_write(name)
            sn.state.add_memlet_path(
                stencil,
                write,
                memlet = dace.Memlet.simple(name, memlet_subset),
                src_conn = name + '_out',
                propagate=True
            )
        return sn


def FillMaps(stencils: list, sdfg, id_resolver):
    MapFiller(sdfg, id_resolver).visit(stencils)



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

    # Code transformations
    ReplaceKeywords(stencils) # Prevents name collisions. 'in' -> 'in_'
    ExpandAssignmentOperator(stencils) # Makes data flow explicit. 'a += b' -> 'a = a + b'
    UnparseCode(stencils, id_resolver) # C++ AST -> Python string
    RenameVariables(stencils) # 'a = a' -> 'a_out = a_in'

    # TODO: Move these two.
    AdaptToMemoryLayout(stencils)
    RemoveUnusedDimensions(stencils, id_resolver) # 'a[0,0,0] = b2D[0,0,0]' -> 'a[0,0,0] = b2D[0,0]'

    # Tree transformations
    Group_by_K_Intervals(stencils) # Sorts control flow. (Stages x DoMethods) -> K_Sections
    ReplaceMultiStages(stencils) # MultiStages -> (Map, Loop)
    IntroduceStencilNode(stencils, id_resolver) # Statements -> StencilNode

    global_sdfg = dace.SDFG(metadata.stencilName)

    gi = AddGlobalInit(global_sdfg, id_resolver, 
        { id : stencilInstantiation.internalIR.globalVariableToValue[id_resolver.GetName(id)].value for id in metadata.globalVariableIDs })
    AddControlFlow(stencils, global_sdfg, gi, id_resolver)
    #ConnectMapDummies(stencils, global_sdfg)
    FillMaps(stencils, global_sdfg, id_resolver)
    ConnectLoopDummies(stencils, global_sdfg)

    # exp = Exporter(id_resolver, global_sdfg)

    # exp.try_add_array(global_sdfg, metadata.APIFieldIDs) # Adds API fields
    # exp.try_add_transient(global_sdfg, metadata.temporaryFieldIDs) #TODO: Check if this is the right place to add them. Also what are temporaries?
    
    # exp.Export_Globals({ id : stencilInstantiation.internalIR.globalVariableToValue[id_resolver.GetName(id)].value for id in metadata.globalVariableIDs })
    # exp.Export_Stencils(stencils)

    # sdfg.fill_scope_connectors()
    return global_sdfg

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

    
