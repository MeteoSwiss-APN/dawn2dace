import dace
from stencilflow.stencil.stencil import Stencil as StencilLib
import sympy
from itertools import chain
from IndexHandling import *
from Intermediates import *
from IdResolver import IdResolver

I = dace.symbol("I")
J = dace.symbol("J")
K = dace.symbol("K")
halo = dace.symbol("halo")
data_type = dace.float64

def dim_filter(dimensions:Index3D, i, j, k) -> tuple:
    dim_mem = ToMemLayout(dimensions.i, dimensions.j, dimensions.k)
    return (elem for dim, elem in zip(dim_mem, ToMemLayout(i, j, k)) if dim)

class Exporter:
    def __init__(self, id_resolver:IdResolver, sdfg):
        self.id_resolver = id_resolver
        self.sdfg = sdfg
        self.last_state_ = None

    def try_add_scalar(self, sdfg, ids):
        if not isinstance(ids, list):
            ids = list(ids)
        
        for id in ids:
            name = self.id_resolver.GetName(id)

            if self.id_resolver.IsALiteral(id):
                continue

            #print("Try add scalar: {}".format(name))

            try:
                sdfg.add_scalar(name, dtype=data_type)
            except:
                pass

    def try_add_array(self, sdfg, ids):
        if not isinstance(ids, list):
            ids = list(ids)
        
        for id in ids:
            name = self.id_resolver.GetName(id)
            shape = self.GetShape(id)
            strides = self.GetStrides(id)
            total_size = self.GetTotalSize(id)

            if self.id_resolver.IsALiteral(id):
                continue

            #print("Try add array: {} of size {} with strides {} and total size {}".format(name, shape, strides, total_size))

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

    def try_add_transient(self, sdfg, ids):
        if not isinstance(ids, list):
            ids = list(ids)
        
        for id in ids:
            name = self.id_resolver.GetName(id)
            shape = self.GetShape(id)
            strides = self.GetStrides(id)
            total_size = self.GetTotalSize(id)

            if self.id_resolver.IsALiteral(id):
                continue

            # print("Try add transient: {} of size {} with strides {} and total size {}".format(name, shape, strides, total_size))

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

    def Export_Globals(self, id_value:dict):
        if not id_value:
            return

        init_state = self.sdfg.add_state("GlobalInit")

        for id, value in id_value.items():
            name = self.id_resolver.GetName(id)
            self.sdfg.add_scalar(name, dtype=data_type, transient=True)

            op2 = init_state.add_write(name)
            tasklet = init_state.add_tasklet(name,
                inputs=None,
                outputs={name},
                code="{} = {}".format(name, value)
            )
            out_memlet = dace.Memlet.simple(name, '0')
            init_state.add_edge(tasklet, name, op2, None, out_memlet)

        if self.last_state_ is not None:
            self.sdfg.add_edge(self.last_state_, init_state, dace.InterstateEdge())
        self.last_state_ = init_state

    def GetShape(self, id:int) -> list:
        ret = dim_filter(self.id_resolver.GetDimensions(id), I, J, K + 1)
        if ret:
            return list(ret)
        return [1]

    def GetStrides(self, id:int) -> list:
        dim = self.id_resolver.GetDimensions(id)
        highest, middle, lowest = ToMemLayout(*ToStridePolicy3D(
            I if dim.i else 0,
            J if dim.j else 0,
            K+1 if dim.k else 0
        ))
        if lowest:
            if middle:
                if highest:
                    return [middle * lowest, lowest, 1]
                else:
                    return [lowest, 1]
            else:
                if highest:
                    return [lowest, 1]
                else:
                    return [1]
        else:
            if middle:
                if highest:
                    return [middle, 1]
                else:
                    return [1]
            else:
                if highest:
                    return [1]
                else:
                    return [1]

    def GetTotalSize(self, id:int) -> int:
        first_order_stride = self.GetStrides(id)[0]

        dim = self.id_resolver.GetDimensions(id)
        highest, middle, lowest = ToMemLayout(
            I if dim.i else 0,
            J if dim.j else 0,
            K if dim.k else 0
        )

        for x in [highest, middle, lowest]:
            if x != 0:
                return x * first_order_stride

    def Export_MemoryAccess3D(self, id:int, mem_acc:MemoryAccess3D, relative_to_k) -> str:
        if not isinstance(mem_acc, MemoryAccess3D):
            raise TypeError("Expected MemoryAccess3D, got: {}".format(type(mem_acc).__name__))
        
        dims = self.id_resolver.GetDimensions(id)
        if (dims.i == 0) and (dims.j == 0) and (dims.k == 0):
            return "0"

        i_str = "i+{}:i+{}".format(mem_acc.i.lower, mem_acc.i.upper + 1)
        j_str = "j+{}:j+{}".format(mem_acc.j.lower, mem_acc.j.upper + 1)
        if relative_to_k:
            k_str = "k+{}:k+{}".format(mem_acc.k.lower, mem_acc.k.upper + 1)
        else:
            k_str = "{}:{}".format(mem_acc.k.lower, mem_acc.k.upper + 1)
        
        return ', '.join(dim_filter(dims, i_str, j_str, k_str))

    def Export_Accesses(self, id:int, mem_acc:MemoryAccess3D):
        """
        Returns a pair containing the following two things:
        - A 3-tuple of bools to denote wich dimensions are non-degenerated.
        - A list of accesses where the array is accessed.
        """

        if not isinstance(mem_acc, MemoryAccess3D):
            raise TypeError("Expected MemoryAccess3D, got: {}".format(type(mem_acc).__name__))

        dims = self.id_resolver.GetDimensions(id)

        # TODO: This is the bounding box of all memory accesses, thus suboptimal and can be improved to not include unused data.
        accs = [ToMemLayout(i, j, k) for i in range(mem_acc.i.lower, mem_acc.i.upper + 1)
                                     for j in range(mem_acc.j.lower, mem_acc.j.upper + 1)
                                     for k in range(0, mem_acc.k.upper + 1 - mem_acc.k.lower)]
        dimensions_present = ToMemLayout(
            dims.i != 0,
            dims.j != 0,
            dims.k != 0,
        )
        return (dimensions_present, accs)

    def CreateMemlets(self, transactions:dict, suffix:str, relative_to_k:bool) -> dict:
        memlets = {}
        for id, mem_acc in transactions.items():
            name = self.id_resolver.GetName(id)

            if self.id_resolver.IsALiteral(id):
                continue

            memlets[name + suffix] = dace.Memlet.simple(name, self.Export_MemoryAccess3D(id, mem_acc, relative_to_k))
        return memlets

    def Create_Variable_Access_map(self, transactions:dict, suffix:str) -> dict:
        """ Returns a map of variable names (suffixed) and its saccesses. """
        memlets = {}
        for id, mem_acc in transactions.items():
            name = self.id_resolver.GetName(id)

            if self.id_resolver.IsALiteral(id):
                continue

            memlets[name + suffix] = self.Export_Accesses(id, mem_acc)
        return memlets

    def Export_parallel(self, multi_stage: MultiStage, interval: K_Interval):
        multi_stage_state = self.sdfg.add_state("state_{}".format(CreateUID()))
        sub_sdfg = dace.SDFG("ms_subsdfg{}".format(CreateUID()))
        last_state = None
        # to connect them we need all input and output names
        collected_input_ids = []
        collected_output_ids = []
        for stage in multi_stage.stages:
            for do_method in stage.do_methods:
                if do_method.k_interval != interval:
                    continue

                for stmt in do_method.statements:
                    reads = stmt.reads.keys()
                    writes = stmt.writes.keys()
                    all = reads | writes
                    apis, temporaries, globals, literals, locals = self.id_resolver.Classify(all)

                    self.try_add_array(sub_sdfg, all - locals - globals)
                    self.try_add_transient(sub_sdfg, locals)
                    self.try_add_scalar(sub_sdfg, reads & globals)

                    self.try_add_transient(self.sdfg, all - locals - globals)
                    self.try_add_scalar(self.sdfg, reads & globals)

                    collected_input_ids.extend(reads - literals - locals)
                    collected_output_ids.extend(writes - literals - locals)

                    unoffsetted_read_span = MemoryAccess3D.GetSpan(stmt.unoffsetted_read_spans.values())
                    unoffsetted_write_span = MemoryAccess3D.GetSpan(stmt.unoffsetted_write_spans.values())
                    unoffsetted_span = MemoryAccess3D.GetSpan([unoffsetted_read_span, unoffsetted_write_span])

                    halo_i_lower = -unoffsetted_span.i.lower
                    halo_i_upper = unoffsetted_span.i.upper
                    halo_j_lower = -unoffsetted_span.j.lower
                    halo_j_upper = unoffsetted_span.j.upper

                    # Workaround for missing shape inferance information in IIR.
                    if any(self.id_resolver.IsInAPI(id) for id in stmt.writes.keys()):
                        halo_i_lower = halo
                        halo_i_upper = halo
                        halo_j_lower = halo
                        halo_j_upper = halo

                    boundary_conditions = {
                        self.id_resolver.GetName(id): {
                            "btype": "shrink",
                            "halo": tuple(chain.from_iterable(
                                ToMemLayout(
                                    (halo_i_lower, halo_i_upper), # halo in I
                                    (halo_j_lower, halo_j_upper), # halo in J
                                    (0, 0), # halo in K
                                )))
                            }
                            for id in stmt.reads
                        }

                    state = sub_sdfg.add_state("state_{}".format(CreateUID()))

                    input_fields = self.Create_Variable_Access_map(stmt.reads, '_in')
                    output_fields = self.Create_Variable_Access_map(stmt.writes, '_out')

                    stenc = StencilLib(
                        label = str(stmt),
                        shape = list(ToMemLayout(I, J, 1)),
                        accesses = input_fields,
                        output_fields = output_fields,
                        boundary_conditions = boundary_conditions,
                        code = stmt.code
                    )
                    state.add_node(stenc)
                    
                    # Add stencil-input memlet paths, from state.read to stencil.
                    for id, mem_acc in stmt.reads.items():
                        name = self.id_resolver.GetName(id)
                        dims = self.id_resolver.GetDimensions(id)
                        read = state.add_read(name)
                        input_memlet_subst = ','.join(dim_filter(dims,
                            "0:I",
                            "0:J",
                            "0:{}".format(unoffsetted_read_span.k.lower - unoffsetted_read_span.k.upper + 1),
                        ))
                        if not input_memlet_subst:
                            input_memlet_subst = '0'
                        state.add_memlet_path(
                            read,
                            stenc,
                            memlet = dace.Memlet.simple(name, input_memlet_subst),
                            dst_conn = name + '_in',
                            propagate=True
                        )

                    # Add stencil-output memlet paths, from stencil to state.write.
                    for id, mem_acc in stmt.writes.items():
                        name = self.id_resolver.GetName(id)
                        dims = self.id_resolver.GetDimensions(id)
                        write = state.add_write(name)
                        output_memlet_subst = ','.join(dim_filter(dims,
                            "{}:I-{}".format(halo_i_lower, halo_i_upper),
                            "{}:J-{}".format(halo_j_lower, halo_j_upper),
                            "{}:{}".format(-unoffsetted_write_span.k.lower, -unoffsetted_write_span.k.upper + 1),
                        ))
                        state.add_memlet_path(
                            stenc,
                            write,
                            memlet = dace.Memlet.simple(name, output_memlet_subst),
                            src_conn = name + '_out',
                            propagate=True
                        )
                    
                    # state = sub_sdfg.add_state("state_{}".format(CreateUID()))
                    # state.add_mapped_tasklet(
                    #     str(stmt),
                    #     map_ranges,
                    #     inputs = self.CreateMemlets(stmt.reads, '_in', relative_to_k = False),
                    #     code = stmt.code,
                    #     outputs = self.CreateMemlets(stmt.writes, '_out', relative_to_k = False),
                    #     external_edges = True,
                    #     propagate=True
                    # )

                    # set the state to be the last one to connect them
                    if last_state is not None:
                        sub_sdfg.add_edge(last_state, state, dace.InterstateEdge())
                    last_state = state

        collected_input_names = set(self.id_resolver.GetName(id) for id in collected_input_ids)
        collected_output_names = set(self.id_resolver.GetName(id) for id in collected_output_ids)

        nested_sdfg = multi_stage_state.add_nested_sdfg(
            sub_sdfg, 
            self.sdfg,
            collected_input_names,
            collected_output_names
        )

        map_entry, map_exit = multi_stage_state.add_map("kmap", dict(k=str(interval)))

        # input memlets
        for id in set(collected_input_ids):
            name = self.id_resolver.GetName(id)
            dims = self.id_resolver.GetDimensions(id)

            read = multi_stage_state.add_read(name)
            k_mem_acc = multi_stage.unoffsetted_read_spans[id].k
            subset_str = ', '.join(dim_filter(dims, "0:I", "0:J", "k+{}:k+{}".format(k_mem_acc.lower, k_mem_acc.upper + 1)))
            if not subset_str:
                subset_str = "0"

            # add the reads and the input memlet path : read -> map_entry -> nested_sdfg
            multi_stage_state.add_memlet_path(
                read,
                map_entry,
                nested_sdfg,
                memlet = dace.Memlet.simple(name, subset_str),
                dst_conn = name,
                propagate=True
            )
        if len(collected_input_ids) == 0:
            # If there are no inputs to this SDFG, connect it to the map with an empty memlet
            # to keep it in the scope.
            multi_stage_state.add_edge(map_entry, None, nested_sdfg, None, dace.EmptyMemlet())

        # output memlets
        for id in set(collected_output_ids):
            name = self.id_resolver.GetName(id)
            dims = self.id_resolver.GetDimensions(id)

            write = multi_stage_state.add_write(name)
            k_mem_acc = multi_stage.unoffsetted_write_spans[id].k
            subset_str = ', '.join(dim_filter(dims, "0:I", "0:J", "k+{}:k+{}".format(k_mem_acc.lower, k_mem_acc.upper + 1)))
            if not subset_str:
                subset_str = "0"
            
            # add the writes and the output memlet path : nested_sdfg -> map_exit -> write
            multi_stage_state.add_memlet_path(
                nested_sdfg,
                map_exit,
                write,
                memlet=dace.Memlet.simple(name, subset_str),
                src_conn = name,
                propagate=True
            )

        if self.last_state_ is not None:
            self.sdfg.add_edge(self.last_state_, multi_stage_state, dace.InterstateEdge())

        return multi_stage_state

    def Export_loop(self, multi_stage: MultiStage, interval: K_Interval, execution_order: ExecutionOrder):
        last_state = None
        first_state = None
        # This is the state previous to this ms

        for stage in multi_stage.stages:
            for do_method in stage.do_methods:
                if do_method.k_interval != interval:
                    continue

                for stmt in do_method.statements:
                    self.try_add_transient(self.sdfg, stmt.reads.keys())
                    self.try_add_transient(self.sdfg, stmt.writes.keys())

                    self.try_add_scalar(self.sdfg, (id for id in stmt.reads.keys() if self.id_resolver.IsGlobal(id)))

                    unoffsetted_read_span = MemoryAccess3D.GetSpan(stmt.unoffsetted_read_spans.values())
                    unoffsetted_write_span = MemoryAccess3D.GetSpan(stmt.unoffsetted_write_spans.values())
                    unoffsetted_span = MemoryAccess3D.GetSpan([unoffsetted_read_span, unoffsetted_write_span])

                    halo_i_lower = -unoffsetted_span.i.lower
                    halo_i_upper = unoffsetted_span.i.upper
                    halo_j_lower = -unoffsetted_span.j.lower
                    halo_j_upper = unoffsetted_span.j.upper

                    # Workaround for missing shape inferance information in IIR.
                    if any(self.id_resolver.IsInAPI(id) for id in stmt.writes.keys()):
                        halo_i_lower = halo
                        halo_i_upper = halo
                        halo_j_lower = halo
                        halo_j_upper = halo

                    boundary_conditions = {
                        self.id_resolver.GetName(id): {
                            "btype": "shrink",
                            "halo": tuple(chain.from_iterable(
                                ToMemLayout(
                                    (halo_i_lower, halo_i_upper), # halo in I
                                    (halo_j_lower, halo_j_upper), # halo in J
                                    (0, 0), # halo in K
                                )))
                            }
                            for id in stmt.reads
                        }

                    state = self.sdfg.add_state("state_{}".format(CreateUID()))

                    input_fields = self.Create_Variable_Access_map(stmt.reads, '_in')
                    output_fields = self.Create_Variable_Access_map(stmt.writes, '_out')

                    stenc = StencilLib(
                        label = str(stmt),
                        shape = list(ToMemLayout(I, J, 1)),
                        accesses = self.Create_Variable_Access_map(stmt.reads, '_in'),
                        output_fields = self.Create_Variable_Access_map(stmt.writes, '_out'),
                        boundary_conditions = boundary_conditions,
                        code = stmt.code
                        )

                    state.add_node(stenc)
                    
                    # Add stencil-input memlet paths, from state.read to stencil.
                    for id, mem_acc in stmt.reads.items():
                        name = self.id_resolver.GetName(id)
                        dims = self.id_resolver.GetDimensions(id)
                        read = state.add_read(name)
                        k_mem_acc = stmt.unoffsetted_read_spans[id].k
                        input_memlet_subst = ','.join(dim_filter(dims,
                            "0:I",
                            "0:J",
                            "k+{}:k+{}".format(k_mem_acc.lower, k_mem_acc.upper + 1),
                        ))
                        state.add_memlet_path(
                            read,
                            stenc,
                            memlet = dace.Memlet.simple(name, input_memlet_subst),
                            dst_conn = name + '_in',
                            propagate=True
                        )

                    # Add stencil-output memlet paths, from stencil to state.write.
                    for id, mem_acc in stmt.writes.items():
                        name = self.id_resolver.GetName(id)
                        dims = self.id_resolver.GetDimensions(id)
                        write = state.add_write(name)
                        output_memlet_subst = ','.join(dim_filter(dims,
                            "{}:I-{}".format(halo_i_lower, halo_i_upper),
                            "{}:J-{}".format(halo_j_lower, halo_j_upper),
                            "k+{}:k+{}".format(unoffsetted_write_span.k.lower, unoffsetted_write_span.k.upper + 1),
                        ))
                        state.add_memlet_path(
                            stenc,
                            write,
                            memlet = dace.Memlet.simple(name, output_memlet_subst),
                            src_conn = name + '_out',
                            propagate=True
                        )

                    # Since we're in a sequential loop, we only need a map in i and j
                    # state = self.sdfg.add_state("state_{}".format(CreateUID()))
                    # state.add_mapped_tasklet(
                    #     str(stmt),
                    #     map_ranges,
                    #     inputs = self.CreateMemlets(stmt.reads, '_in', relative_to_k = True),
                    #     code = stmt.code,
                    #     outputs = self.CreateMemlets(stmt.writes, '_out', relative_to_k = True),
                    #     external_edges = True, propagate=True
                    # )

                    if first_state is None:
                        first_state = state

                    if last_state is not None:
                        self.sdfg.add_edge(last_state, state, dace.InterstateEdge())
                    last_state = state

        if execution_order == ExecutionOrder.Forward_Loop.value:
            initialize_expr = interval.begin
            condition_expr = "k < {}".format(interval.end)
            increment_expr = "k + 1"
        else:
            initialize_expr = interval.end + "-1"
            condition_expr = "k >= {}".format(interval.begin)
            increment_expr = "k - 1"

        _, _, last_state  = self.sdfg.add_loop(
            before_state = self.last_state_,
            loop_state = first_state,
            loop_end_state = last_state,
            after_state = None,
            loop_var = "k",
            initialize_expr = initialize_expr,
            condition_expr = condition_expr,
            increment_expr = increment_expr
        )
        return last_state

    
    def Export_MultiStage(self, multi_stage: MultiStage):
        if not isinstance(multi_stage, MultiStage):
            raise TypeError("Expected MultiStage, got: {}".format(type(multi_stage).__name__))

        intervals = set()
        for stage in multi_stage.stages:
            for do_method in stage.do_methods:
                intervals.add(do_method.k_interval)
        intervals = list(intervals)
        
        intervals.sort(
            key = lambda interval: interval.sort_key,
            reverse = (multi_stage.execution_order == ExecutionOrder.Backward_Loop)
        )

        if __debug__:
            print("list of all the intervals:")
            for i in intervals:
                print(i)

        # export the MultiStage for every interval (in loop order)
        for interval in intervals:
            if multi_stage.execution_order == ExecutionOrder.Parallel.value:
            	self.last_state_ = self.Export_parallel(multi_stage, interval)
            else:
            	self.last_state_ = self.Export_loop(multi_stage, interval, multi_stage.execution_order)

    def Export_Stencil(self, stenc:Stencil):
        assert type(stenc) is Stencil
        
        for ms in stenc.multi_stages:
            self.Export_MultiStage(ms)

    def Export_Stencils(self, stenc: list):
        for s in stenc:
            self.Export_Stencil(s)
