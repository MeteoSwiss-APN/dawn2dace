import dace
import dace.data
from stencilflow.stencil.stencil import Stencil as StencilLib
import sympy
from itertools import chain
from Intermediates import *
from IdResolver import IdResolver

I = dace.symbol("I", dtype=dace.int32)
J = dace.symbol("J", dtype=dace.int32)
K = dace.symbol("K", dtype=dace.int32)
halo = dace.symbol("halo", dtype=dace.int32)
float_type = dace.float64

IJK_stride_I = dace.symbol("IJK_stride_I", dtype=dace.int32)
IJK_stride_J = dace.symbol("IJK_stride_J", dtype=dace.int32)
IJK_stride_K = dace.symbol("IJK_stride_K", dtype=dace.int32)
IJK_total_size = dace.symbol("IJK_total_size", dtype=dace.int32)

IJ_stride_I = dace.symbol("IJ_stride_I", dtype=dace.int32)
IJ_stride_J = dace.symbol("IJ_stride_J", dtype=dace.int32)
IJ_total_size = dace.symbol("IJ_total_size", dtype=dace.int32)

I_total_size = dace.symbol("I_total_size", dtype=dace.int32)
J_total_size = dace.symbol("J_total_size", dtype=dace.int32)
K_total_size = dace.symbol("K_total_size", dtype=dace.int32)

def dim_filter(dim:Any3D, i, j, k) -> tuple:
    return tuple(elem for dim, elem in zip(dim, [i, j, k]) if dim)

class Exporter:
    def __init__(self, id_resolver:IdResolver, name:str):
        self.id_resolver = id_resolver
        self.sdfg = dace.SDFG(name)
        self.sdfg.add_symbol('I', stype=dace.int32)
        self.sdfg.add_symbol('J', stype=dace.int32)
        self.sdfg.add_symbol('K', stype=dace.int32)
        self.sdfg.add_symbol('halo', stype=dace.int32)
        self.sdfg.add_symbol("IJK_stride_I", stype=dace.int32)
        self.sdfg.add_symbol("IJK_stride_J", stype=dace.int32)
        self.sdfg.add_symbol("IJK_stride_K", stype=dace.int32)
        self.sdfg.add_symbol("IJK_total_size", stype=dace.int32)
        self.sdfg.add_symbol("IJ_stride_I", stype=dace.int32)
        self.sdfg.add_symbol("IJ_stride_J", stype=dace.int32)
        self.sdfg.add_symbol("IJ_total_size", stype=dace.int32)
        self.sdfg.add_symbol("I_total_size", stype=dace.int32)
        self.sdfg.add_symbol("J_total_size", stype=dace.int32)
        self.sdfg.add_symbol("K_total_size", stype=dace.int32)
        self.last_state_ = None

    def Name(self, id:int) -> str:
        return self.id_resolver.GetName(id)

    def Dimensions(self, id:int) -> Bool3D:
        """ Returns if the dimensions (i,j,k) are present in this field. """
        return self.id_resolver.GetDimensions(id)

    def Shape(self, id:int) -> list:
        return list(dim_filter(self.Dimensions(id), I, J, K+1) or [1])

    def Strides(self, id:int) -> list:
        return {
            Bool3D(True, True, True) : [IJK_stride_I, IJK_stride_J, IJK_stride_K],
            Bool3D(True, True, False) : [IJ_stride_I, IJ_stride_J],
            Bool3D(True, False, False) : [1],
            Bool3D(False, True, False) : [1],
            Bool3D(False, False, True) : [1],
            Bool3D(False, False, False) : [1]
        }[self.Dimensions(id)]

    def TotalSize(self, id:int):
        return {
            Bool3D(True, True, True) : IJK_total_size,
            Bool3D(True, True, False) : IJ_total_size,
            Bool3D(True, False, False) : I_total_size,
            Bool3D(False, True, False) : J_total_size,
            Bool3D(False, False, True) : K_total_size,
            Bool3D(False, False, False) : 1
        }[self.Dimensions(id)]

    def TryAddScalar(self, sdfg, ids):
        for id in ids:
            name = self.Name(id)

            try:
                sdfg.add_scalar(name, dtype=float_type)
                print(f'Added scalar: {name}')
            except:
                pass

    def TryAddArray(self, sdfg, ids, transient:bool=False):
        for id in ids:
            name = self.Name(id)
            shape = self.Shape(id)
            strides = self.Strides(id)
            total_size = self.TotalSize(id)

            try:
                sdfg.add_array(
                    name, 
                    shape, 
                    dtype=float_type,
                    transient=transient,
                    strides=strides, 
                    total_size=total_size
                )
                print(f'Added {"transient" if transient else "array"}: {name} of size {shape} with strides {strides} and total size {total_size}')
            except:
                pass

    def Export_ApiFields(self, ids):
        self.TryAddArray(self.sdfg, ids)

    def Export_TemporaryFields(self, ids):
        self.TryAddArray(self.sdfg, ids, transient=True)

    def Export_Globals(self, id_value: dict):
        for id, value in id_value.items():
            name = self.Name(id)
            self.sdfg.add_constant(name, value, dtype=dace.data.Scalar(float_type))

    def Export_Accesses(self, id:int, mem_acc:ClosedInterval3D):
        """
        Returns a pair containing the following two things:
        - A 3-tuple of bools to denote wich dimensions are not degenerated.
        - A list of accesses where the array is accessed.
        """

        dims = self.Dimensions(id)

        #This is the bounding box of all memory accesses
        accs = [ dim_filter(dims, i, j, k) for i,j,k in mem_acc.range() ]
        dimensions_present = dims.to_tuple()
        return dimensions_present, accs

    def Create_Variable_Access_map(self, transactions:dict, suffix:str) -> dict:
        """ Returns a map of variable names (suffixed) and its accesses. """
        return { self.Name(id) + suffix : self.Export_Accesses(id, acc)
            for id, acc in transactions.items()
            }

    def Export_parallel(self, multi_stage: MultiStage):
        ms_state = self.sdfg.add_state(f'ms_state_{CreateUID()}')
        ms_sdfg = dace.SDFG(f'ms_sdfg_{CreateUID()}')
        last_state = None
        
        for stage in multi_stage.stages:
            for do_method in stage.do_methods:
                reads = do_method.ReadIds()
                writes = do_method.WriteIds()
                all = reads | writes
                globals = { id for id in all if self.id_resolver.IsGlobal(id) }

                self.TryAddArray(ms_sdfg, all - globals)
                # self.TryAddScalar(ms_sdfg, reads & globals)

                self.TryAddArray(self.sdfg, all - globals, transient=True)
                # self.TryAddScalar(self.sdfg, reads & globals)
                
                halo = ClosedInterval3D(Symbol('halo'),Symbol('halo'),Symbol('halo'),Symbol('halo'),0,0)
                halo -= stage.extents
                bc_dict = { "btype" : "shrink", "halo" : halo.to_6_tuple() }
                boundary_conditions = { f'{self.Name(id)}_out' : bc_dict for id in writes }

                state = ms_sdfg.add_state(str(do_method))

                stenc = StencilLib(
                    label = str(do_method),
                    shape = [I, J, 1],
                    accesses = self.Create_Variable_Access_map(do_method.Reads(), '_in'), # input fields
                    output_fields = self.Create_Variable_Access_map(do_method.Writes(), '_out'), # output fields
                    boundary_conditions = boundary_conditions,
                    code = do_method.Code()
                )
                stenc.implementation = 'CPU'
                state.add_node(stenc)
                
                # Add memlet path from state.read to stencil.
                for id, acc in do_method.read_memlets.items():
                    name = self.Name(id)
                    dims = self.Dimensions(id)
                    subset = ','.join(dim_filter(dims, '0:I', '0:J', HalfOpenIntervalStr(acc.k))) or '0'
                    
                    state.add_memlet_path(
                        state.add_read(name),
                        stenc,
                        memlet = dace.Memlet(f'{name}[{subset}]'),
                        dst_conn = name + '_in',
                        propagate=True
                    )

                # Add memlet path from stencil to state.write.
                for id, acc in do_method.write_memlets.items():
                    name = self.Name(id)
                    dims = self.Dimensions(id)
                    subset = ','.join(dim_filter(dims, '0:I', '0:J', HalfOpenIntervalStr(acc.k))) or '0'

                    state.add_memlet_path(
                        stenc,
                        state.add_write(name),
                        memlet = dace.Memlet(f'{name}[{subset}]'),
                        src_conn = name + '_out',
                        propagate=True
                    )

                # set the state to be the last one to connect them
                if last_state is not None:
                    ms_sdfg.add_edge(last_state, state, dace.InterstateEdge())
                last_state = state

        read_ids = multi_stage.ReadIds()
        write_ids = multi_stage.WriteIds()

        read_names = set(self.Name(id) for id in read_ids)
        write_names = set(self.Name(id) for id in write_ids)

        nested_sdfg = ms_state.add_nested_sdfg(
            ms_sdfg, 
            self.sdfg,
            read_names,
            write_names,
            {'halo' : dace.symbol('halo'), 'I' : dace.symbol('I'), 'J' : dace.symbol('J'), 'K' : dace.symbol('K'),
            'IJK_stride_I' : dace.symbol('IJK_stride_I'),
            'IJK_stride_J' : dace.symbol('IJK_stride_J'),
            'IJK_stride_K' : dace.symbol('IJK_stride_K'),
            'IJK_total_size' : dace.symbol('IJK_total_size'),
            'IJ_stride_I' : dace.symbol('IJ_stride_I'),
            'IJ_stride_J' : dace.symbol('IJ_stride_J'),
            'IJ_total_size' : dace.symbol('IJ_total_size'),
            'I_total_size' : dace.symbol('I_total_size'),
            'J_total_size' : dace.symbol('J_total_size'),
            'K_total_size' : dace.symbol('K_total_size')}
        )

        map_entry, map_exit = ms_state.add_map("kmap", { 'k' : str(do_method.k_interval) })

        for id, acc in multi_stage.read_memlets.items():
            if id not in read_ids:
                continue
            name = self.Name(id)
            dims = self.Dimensions(id)
            subset = ','.join(dim_filter(dims, '0:I', '0:J', f'k+{acc.k.lower}:k+{acc.k.upper+1}')) or '0'

            # add the reads and the input memlet path : read -> map_entry -> nested_sdfg
            ms_state.add_memlet_path(
                ms_state.add_read(name),
                map_entry,
                nested_sdfg,
                memlet = dace.Memlet(f'{name}[{subset}]'),
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
            name = self.Name(id)
            dims = self.Dimensions(id)
            subset = ','.join(dim_filter(dims, '0:I', '0:J', f'k+{acc.k.lower}:k+{acc.k.upper+1}')) or '0'
            
            # add the writes and the output memlet path : nested_sdfg -> map_exit -> write
            ms_state.add_memlet_path(
                nested_sdfg,
                map_exit,
                ms_state.add_write(name),
                memlet = dace.Memlet(f'{name}[{subset}]'),
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

                self.TryAddArray(self.sdfg, all - globals, transient=True)
                # self.TryAddScalar(self.sdfg, reads & globals)

                halo = ClosedInterval3D(Symbol('halo'),Symbol('halo'),Symbol('halo'),Symbol('halo'),0,0)
                halo -= stage.extents
                bc_dict = { "btype" : "shrink", "halo" : halo.to_6_tuple() }
                boundary_conditions = { f'{self.Name(id)}_out' : bc_dict for id in writes }

                state = self.sdfg.add_state(str(do_method))

                stenc = StencilLib(
                    label = str(do_method),
                    shape = [I, J, 1],
                    accesses = self.Create_Variable_Access_map(do_method.Reads(), '_in'), # input fields
                    output_fields = self.Create_Variable_Access_map(do_method.Writes(), '_out'), # output fields
                    boundary_conditions = boundary_conditions,
                    code = do_method.Code()
                )
                stenc.implementation = 'CPU'
                state.add_node(stenc)
                
                # Add memlet path from state.read to stencil.
                for id, acc in do_method.read_memlets.items():
                    name = self.Name(id)
                    dims = self.Dimensions(id)
                    subset = ','.join(dim_filter(dims, '0:I', '0:J', f'k+{acc.k.lower}:k+{acc.k.upper+1}')) or '0'

                    state.add_memlet_path(
                        state.add_read(name),
                        stenc,
                        memlet = dace.Memlet(f'{name}[{subset}]'),
                        dst_conn = name + '_in',
                        propagate=True
                    )

                # Add memlet path from stencil to state.write.
                for id, acc in do_method.write_memlets.items():
                    name = self.Name(id)
                    dims = self.Dimensions(id)
                    subset = ','.join(dim_filter(dims, '0:I', '0:J', f'k+{acc.k.lower}:k+{acc.k.upper+1}')) or '0'

                    state.add_memlet_path(
                        stenc,
                        state.add_write(name),
                        memlet = dace.Memlet(f'{name}[{subset}]'),
                        src_conn = name + '_out',
                        propagate=True
                    )

                if first_state is None:
                    first_state = state

                if last_state is not None:
                    self.sdfg.add_edge(last_state, state, dace.InterstateEdge())
                last_state = state

        if execution_order == ExecutionOrder.Forward_Loop.value:
            initialize_expr = str(do_method.k_interval.lower)
            condition_expr = f'k < {do_method.k_interval.upper}'
            increment_expr = 'k + 1'
        else:
            initialize_expr = str(do_method.k_interval.upper - 1)
            condition_expr = f'k >= {do_method.k_interval.lower}'
            increment_expr = 'k - 1'

        print(initialize_expr, condition_expr, increment_expr)

        _, _, last_state  = self.sdfg.add_loop(
            before_state = self.last_state_,
            loop_state = first_state,
            loop_end_state = last_state,
            after_state = None,
            loop_var = 'k',
            initialize_expr = initialize_expr,
            condition_expr = condition_expr,
            increment_expr = increment_expr
        )
        return last_state

    
    def Export_MultiStage(self, multi_stage: MultiStage):
        if multi_stage.execution_order == ExecutionOrder.Parallel.value:
            self.last_state_ = self.Export_parallel(multi_stage)
        else:
            self.last_state_ = self.Export_loop(multi_stage, multi_stage.execution_order)

    def Export_Stencil(self, stenc:Stencil):
        for ms in stenc.multi_stages:
            self.Export_MultiStage(ms)

    def Export_Stencils(self, stenc: list):
        for s in stenc:
            self.Export_Stencil(s)
