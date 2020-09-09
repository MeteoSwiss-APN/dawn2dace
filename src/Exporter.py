import dace
import dace.data
from stencilflow.stencil.stencil import Stencil as StencilLib
import sympy
from itertools import chain
from IndexHandling import *
from Intermediates import *
from IdResolver import IdResolver

I = dace.symbol("I", dtype=dace.int32)
J = dace.symbol("J", dtype=dace.int32)
K = dace.symbol("K", dtype=dace.int32)
halo = dace.symbol("halo", dtype=dace.int32)
data_type = dace.float64

def dim_filter(dimensions:Index3D, i, j, k) -> tuple:
    dim_mem = ToMemLayout(dimensions.i, dimensions.j, dimensions.k)
    return tuple(elem for dim, elem in zip(dim_mem, ToMemLayout(i, j, k)) if dim)

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

            print("Try add scalar: {}".format(name))

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

    def Export_Globals(self, id_value: dict):
        if not id_value:
            return

        #init_state = self.sdfg.add_state("GlobalInit")

        for id, value in id_value.items():
            name = self.id_resolver.GetName(id)
            self.sdfg.add_constant(name, value, dtype=dace.data.Scalar(data_type))
            # self.sdfg.add_scalar(name, dtype=data_type, transient=True)

            # tasklet = init_state.add_tasklet(
            #     name,
            #     inputs = None,
            #     outputs = { name + '_out' },
            #     code = "{}_out = {}".format(name, value)
            # )
            # init_state.add_memlet_path(
            #     tasklet,
            #     init_state.add_write(name),
            #     memlet = dace.Memlet(name),
            #     src_conn = name + '_out',
            #     propagate = True)

        #if self.last_state_ is not None:
        #    self.sdfg.add_edge(self.last_state_, init_state, dace.InterstateEdge())
        #self.last_state_ = init_state

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

    def Export_Accesses(self, id:int, mem_acc:ClosedInterval3D):
        """
        Returns a pair containing the following two things:
        - A 3-tuple of bools to denote wich dimensions are non-degenerated.
        - A list of accesses where the array is accessed.
        """

        if not isinstance(mem_acc, ClosedInterval3D):
            raise TypeError("Expected ClosedInterval3D, got: {}".format(type(mem_acc).__name__))

        dims = self.id_resolver.GetDimensions(id)

        # TODO: This is the bounding box of all memory accesses, thus suboptimal and can be improved to not include unused data.
        accs = [ dim_filter(dims, i, j, k) for i,j,k in mem_acc.range() ]
        dimensions_present = ToMemLayout(
            dims.i != 0,
            dims.j != 0,
            dims.k != 0,
        )
        return dimensions_present, accs

    def Create_Variable_Access_map(self, transactions:dict, suffix:str) -> dict:
        """ Returns a map of variable names (suffixed) and its accesses. """
        return { self.id_resolver.GetName(id) + suffix : self.Export_Accesses(id, acc)
            for id, acc in transactions.items()
            }

    def Export_parallel(self, multi_stage: MultiStage):
        ms_state = self.sdfg.add_state("ms_state_{}".format(CreateUID()))
        ms_sdfg = dace.SDFG("ms_sdfg_{}".format(CreateUID()))
        last_state = None
        
        for stage in multi_stage.stages:
            for do_method in stage.do_methods:
                reads = do_method.ReadIds()
                writes = do_method.WriteIds()
                all = reads | writes
                globals = { id for id in all if self.id_resolver.IsGlobal(id) }

                self.try_add_array(ms_sdfg, all - globals)
                self.try_add_scalar(ms_sdfg, reads & globals)

                self.try_add_transient(self.sdfg, all - globals)
                self.try_add_scalar(self.sdfg, reads & globals)

                boundary_conditions = {}
                for id in writes:
                    name = self.id_resolver.GetName(id) + '_out'
                    halo = ClosedInterval3D(Symbol('halo'),Symbol('halo'),Symbol('halo'),Symbol('halo'),0,0) - stage.extents
                    x,y,z = ToMemLayout(halo.i, halo.j, halo.k)
                    boundary_conditions[name] = {
                        "btype" : "shrink",
                        "halo" : (x.lower, x.upper, y.lower, y.upper, z.lower, z.upper)
                        }

                state = ms_sdfg.add_state(str(do_method))

                stenc = StencilLib(
                    label = str(do_method),
                    shape = list(ToMemLayout(I, J, 1)),
                    accesses = self.Create_Variable_Access_map(do_method.Reads(), '_in'), # input fields
                    output_fields = self.Create_Variable_Access_map(do_method.Writes(), '_out'), # output fields
                    boundary_conditions = boundary_conditions,
                    code = do_method.Code()
                )
                state.add_node(stenc)
                
                # Add memlet path from state.read to stencil.
                for id, acc in do_method.read_memlets.items():
                    name = self.id_resolver.GetName(id)
                    dims = self.id_resolver.GetDimensions(id)
                    subset = ','.join(dim_filter(dims,
                        "0:I",
                        "0:J",
                        HalfOpenIntervalStr(acc.k),
                    ))
                    if not subset:
                        subset = '0'
                        
                    state.add_memlet_path(
                        state.add_read(name),
                        stenc,
                        memlet = dace.Memlet('{}[{}]'.format(name, subset)),
                        dst_conn = name + '_in',
                        propagate=True
                    )

                # Add memlet path from stencil to state.write.
                for id, acc in do_method.write_memlets.items():
                    name = self.id_resolver.GetName(id)
                    dims = self.id_resolver.GetDimensions(id)
                    subset = ','.join(dim_filter(dims,
                        "0:I",
                        "0:J",
                        # "{}:{}".format(-acc.i.lower, Symbol('I') - acc.i.upper),
                        # "{}:{}".format(-acc.j.lower, Symbol('J') - acc.j.upper),
                        HalfOpenIntervalStr(acc.k),
                    ))
                    if not subset:
                        subset = "0"

                    state.add_memlet_path(
                        stenc,
                        state.add_write(name),
                        memlet = dace.Memlet('{}[{}]'.format(name, subset)),
                        src_conn = name + '_out',
                        propagate=True
                    )
                
                # state = ms_sdfg.add_state("state_{}".format(CreateUID()))
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
                    ms_sdfg.add_edge(last_state, state, dace.InterstateEdge())
                last_state = state

        read_ids = multi_stage.ReadIds()
        write_ids = multi_stage.WriteIds()

        read_names = set(self.id_resolver.GetName(id) for id in read_ids)
        write_names = set(self.id_resolver.GetName(id) for id in write_ids)

        nested_sdfg = ms_state.add_nested_sdfg(
            ms_sdfg, 
            self.sdfg,
            read_names,
            write_names,
            {'halo' : dace.symbol('halo'), 'I' : dace.symbol('I'), 'J' : dace.symbol('J'), 'K' : dace.symbol('K')}
        )

        map_entry, map_exit = ms_state.add_map("kmap", { 'k' : str(do_method.k_interval) })

        for id, acc in multi_stage.read_memlets.items():
            if id not in read_ids:
                continue
            name = self.id_resolver.GetName(id)
            dims = self.id_resolver.GetDimensions(id)
            subset = ', '.join(dim_filter(dims, "0:I", "0:J", "k+{}:k+{}".format(acc.k.lower, acc.k.upper + 1)))
            if not subset:
                subset = "0"

            # add the reads and the input memlet path : read -> map_entry -> nested_sdfg
            ms_state.add_memlet_path(
                ms_state.add_read(name),
                map_entry,
                nested_sdfg,
                memlet = dace.Memlet('{}[{}]'.format(name, subset)),
                dst_conn = name,
                propagate=True
            )
        if len(read_ids) == 0:
            # If there are no inputs to this SDFG, connect it to the map with an empty memlet
            # to keep it in the scope.
            ms_state.add_edge(map_entry, None, nested_sdfg, None, dace.memlet.Memlet())

        # output memlets
        for id, acc in multi_stage.write_memlets.items():
            if id not in write_ids:
                continue
            name = self.id_resolver.GetName(id)
            dims = self.id_resolver.GetDimensions(id)
            subset = ', '.join(dim_filter(dims, "0:I", "0:J", "k+{}:k+{}".format(acc.k.lower, acc.k.upper + 1)))
            if not subset:
                subset = "0"
            
            # add the writes and the output memlet path : nested_sdfg -> map_exit -> write
            ms_state.add_memlet_path(
                nested_sdfg,
                map_exit,
                ms_state.add_write(name),
                memlet = dace.Memlet('{}[{}]'.format(name, subset)),
                src_conn = name,
                propagate=True
            )

        if self.last_state_ is not None:
            self.sdfg.add_edge(self.last_state_, ms_state, dace.InterstateEdge())

        return ms_state

    def Export_loop(self, multi_stage: MultiStage, execution_order: ExecutionOrder):
        last_state = None
        first_state = None
        # This is the state previous to this ms

        for stage in multi_stage.stages:
            for do_method in stage.do_methods:
                reads = do_method.ReadIds()
                writes = do_method.WriteIds()
                all = reads | writes
                globals = { id for id in all if self.id_resolver.IsGlobal(id) }

                self.try_add_transient(self.sdfg, all - globals)
                self.try_add_scalar(self.sdfg, reads & globals)

                boundary_conditions = {}
                for id in writes:
                    name = self.id_resolver.GetName(id) + '_out'
                    halo = ClosedInterval3D(Symbol('halo'),Symbol('halo'),Symbol('halo'),Symbol('halo'),0,0) - stage.extents
                    x,y,z = ToMemLayout(halo.i, halo.j, halo.k)
                    boundary_conditions[name] = {
                        "btype" : "shrink",
                        "halo" : (x.lower, x.upper, y.lower, y.upper, z.lower, z.upper)
                        }

                state = self.sdfg.add_state(str(do_method))

                stenc = StencilLib(
                    label = str(do_method),
                    shape = list(ToMemLayout(I, J, 1)),
                    accesses = self.Create_Variable_Access_map(do_method.Reads(), '_in'), # input fields
                    output_fields = self.Create_Variable_Access_map(do_method.Writes(), '_out'), # output fields
                    boundary_conditions = boundary_conditions,
                    code = do_method.Code()
                )
                state.add_node(stenc)
                
                # Add memlet path from state.read to stencil.
                for id, acc in do_method.read_memlets.items():
                    name = self.id_resolver.GetName(id)
                    dims = self.id_resolver.GetDimensions(id)
                    subset = ','.join(dim_filter(dims,
                        "0:I",
                        "0:J",
                        "k+{}:k+{}".format(acc.k.lower, acc.k.upper + 1),
                    ))
                    if not subset:
                        subset = '0'

                    state.add_memlet_path(
                        state.add_read(name),
                        stenc,
                        memlet = dace.Memlet('{}[{}]'.format(name, subset)),
                        dst_conn = name + '_in',
                        propagate=True
                    )

                # Add memlet path from stencil to state.write.
                for id, acc in do_method.write_memlets.items():
                    name = self.id_resolver.GetName(id)
                    dims = self.id_resolver.GetDimensions(id)
                    subset = ','.join(dim_filter(dims,
                        "0:I",
                        "0:J",
                        "k+{}:k+{}".format(acc.k.lower, acc.k.upper + 1),
                    ))
                    if not subset:
                        subset = '0'

                    state.add_memlet_path(
                        stenc,
                        state.add_write(name),
                        memlet = dace.Memlet('{}[{}]'.format(name, subset)),
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
            initialize_expr = str(do_method.k_interval.lower)
            condition_expr = "k < {}".format(do_method.k_interval.upper)
            increment_expr = "k + 1"
        else:
            initialize_expr = str(do_method.k_interval.upper - 1)
            condition_expr = "k >= {}".format(do_method.k_interval.lower)
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

        # intervals = list(set(do_method.k_interval
        #     for stage in multi_stage.stages
        #     for do_method in stage.do_methods
        #     ))
        
        # intervals.sort(
        #     key = lambda interval: FullEval(interval.lower, 'K', 1000),
        #     reverse = (multi_stage.execution_order == ExecutionOrder.Backward_Loop)
        # )

        # if __debug__:
        #     print("list of all the intervals:")
        #     for i in intervals:
        #         print(i)

        # # export the MultiStage for every interval (in loop order)
        # for interval in intervals:
        if multi_stage.execution_order == ExecutionOrder.Parallel.value:
            self.last_state_ = self.Export_parallel(multi_stage)
        else:
            self.last_state_ = self.Export_loop(multi_stage, multi_stage.execution_order)

    def Export_Stencil(self, stenc:Stencil):
        assert type(stenc) is Stencil
        
        for ms in stenc.multi_stages:
            self.Export_MultiStage(ms)

    def Export_Stencils(self, stenc: list):
        for s in stenc:
            self.Export_Stencil(s)
