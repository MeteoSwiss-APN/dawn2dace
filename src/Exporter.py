import dace
from Intermediates import *
from IdResolver import IdResolver

I = dace.symbol("I")
J = dace.symbol("J")
K = dace.symbol("K")
halo_size = dace.symbol("haloSize")
data_type = dace.float64

def try_add_array(sdfg, name, shape):
    print("Try add array: {} of size [{}]".format(name, ','.join(str(shape))))
    try:
        sdfg.add_array(name, shape, dtype=data_type)
    except:
        pass

def try_add_transient(sdfg, name, shape):
    print("Try add transient: {} of size [{}]".format(name, ','.join(str(shape))))
    try:
        sdfg.add_transient(name, shape, dtype=data_type)
    except:
        pass

class Exporter:
    def __init__(self, id_resolver:IdResolver, sdfg):
        self.id_resolver = id_resolver
        self.sdfg = sdfg
        self.last_state_ = None

    def GetShape(self, id:int):
        dim = self.id_resolver.GetDimensions(id)
        ret = []
        if dim[0]:
            ret.append(I)
        if dim[1]:
            ret.append(J)
        if dim[2]:
            ret.append(K)
        if ret:
            return ret
        return [1]

    def Export_MemoryAccess3D(self, mem_acc:MemoryAccess3D, with_k = True) -> str:
        if not isinstance(mem_acc, MemoryAccess3D):
            raise TypeError("Expected MemoryAccess3D, got: {}".format(type(mem_acc).__name__))

        if mem_acc is None:
            return "0"

        if with_k:
            template = "i+{}:i+{}, j+{}:j+{}, k+{}:k+{}"
        else:
            template = " i+{}:i+{}, j+{}:j+{}, {}:{}"

        return template.format(
            mem_acc.i.lower, mem_acc.i.upper + 1,
            mem_acc.j.lower, mem_acc.j.upper + 1,
            mem_acc.k.lower, mem_acc.k.upper + 1,
        )

    def Export_parallel(self, multi_stage: MultiStage, interval: K_Interval):
        multi_stage_state = self.sdfg.add_state("state_{}".format(CreateUID()))
        sub_sdfg = dace.SDFG("ms_subsdfg{}".format(CreateUID()))
        last_state = None
        # to connect them we need all input and output names
        collected_input_mapping = {}
        collected_output_mapping = {}
        for stage in multi_stage.stages:
            for do_method in stage.do_methods:
                if do_method.k_interval != interval:
                    continue

                for stmt in do_method.statements:
                    state = sub_sdfg.add_state("state_{}".format(CreateUID()))
                    
                    # Creation of the Memlet in the state
                    input_memlets = {}
                    output_memlets = {}

                    for id, read in stmt.reads.items():
                        name = self.id_resolver.GetName(id)
                        shape = self.GetShape(id)

                        if self.id_resolver.IsALiteral(id):
                            continue
                        elif self.id_resolver.IsATemporary(id):
                            access_pattern = "0"
                        elif self.id_resolver.IsGlobal(id):
                            continue
                        elif self.id_resolver.IsLocal(id):
                            name = name[8:-3]
                        else:
                            access_pattern = self.Export_MemoryAccess3D(read, with_k = False)

                        try_add_array(sub_sdfg, name + "_S", shape)

                        input_memlets[name + '_in'] = dace.Memlet.simple(name + "_S", access_pattern)

                        try_add_transient(self.sdfg, name, shape)
                        collected_input_mapping[name + "_S"] = name

                    for id, write in stmt.writes.items():
                        name = self.id_resolver.GetName(id)
                        shape = self.GetShape(id)

                        if self.id_resolver.IsALiteral(id):
                            continue
                        elif self.id_resolver.IsATemporary(id):
                            access_pattern = "0"
                        elif self.id_resolver.IsGlobal(id):
                            continue
                        elif self.id_resolver.IsLocal(id):
                            name = name[8:-3]
                        else:
                            access_pattern = self.Export_MemoryAccess3D(write, with_k = False)

                        try_add_array(sub_sdfg, name + "_S", shape)
                        output_memlets[name + '_out'] = dace.Memlet.simple(name + "_S", access_pattern)

                        try_add_transient(self.sdfg, name, shape)
                        collected_output_mapping[name + "_S"] = name

                    if stmt.code:
                        # The memlet is only in ijk if the do-method is parallel, otherwise we have a loop and hence
                        # the maps are ij-only
                        map_range = dict(i="halo_size:I-halo_size", j="halo_size:J-halo_size")
                        state.add_mapped_tasklet(
                            str(stmt),
                            map_range,
                            input_memlets,
                            stmt.code,
                            output_memlets,
                            external_edges = True
                        )

                    # set the state to be the last one to connect them
                    if last_state is not None:
                        sub_sdfg.add_edge(last_state, state, dace.InterstateEdge())
                    last_state = state

        map_entry, map_exit = multi_stage_state.add_map("kmap", dict(k=str(interval)))
        # fill the sub-sdfg's {in_set} {out_set}
        input_set = collected_input_mapping.keys()
        output_set = collected_output_mapping.keys()
        nested_sdfg = multi_stage_state.add_nested_sdfg(sub_sdfg, self.sdfg, input_set, output_set)

        lower_k = multi_stage.lower_k
        upper_k = multi_stage.upper_k
        # add the reads and the input memlet path : read -> map_entry -> nsdfg
        for sub_sdfg_name, v in collected_input_mapping.items():
            read = multi_stage_state.add_read(v)
            multi_stage_state.add_memlet_path(
                read,
                map_entry,
                nested_sdfg,
                memlet=dace.Memlet.simple(v, "0:I, 0:J, k+{}:k+{}".format(lower_k, upper_k + 1)),
                dst_conn=sub_sdfg_name,
            )
        # add the writes and the output memlet path : nsdfg -> map_exit -> write
        for sub_sdfg_name, v in collected_output_mapping.items():
            write = multi_stage_state.add_write(v)
            multi_stage_state.add_memlet_path(
                nested_sdfg,
                map_exit,
                write,
                memlet=dace.Memlet.simple(v, "0:I, 0:J, k"),
                src_conn=sub_sdfg_name,
            )

        if self.last_state_ is not None:
            self.sdfg.add_edge(self.last_state_, multi_stage_state, dace.InterstateEdge())

        return multi_stage_state

    def Export_loop(self, multi_stage: MultiStage, interval: K_Interval, execution_order: ExecutionOrder):

        first_interval_state = None
        # This is the state previous to this ms
        prev_state = self.last_state_
        for stage in multi_stage.stages:
            for do_method in stage.do_methods:
                if do_method.k_interval != interval:
                    # since we only want to generate stmts for the Do-Methods that are matching the interval, we're ignoring
                    # the other ones
                    continue

                for stmt in do_method.statements:
                    # A State for every stmt makes sure they can be sequential
                    state = self.sdfg.add_state("state_{}".format(CreateUID()))
                    if first_interval_state is None:
                        first_interval_state = state
                    else:
                        self.sdfg.add_edge(self.last_state_, state, dace.InterstateEdge())

                    # Creation of the Memlet in the state
                    input_memlets = {}
                    output_memlets = {}

                    for read in stmt.reads:
                        # Negative ID's are literals and can be skipped.
                        if read.id < 0:
                            continue
                        name = self.id_resolver.GetName(read.id)
                        access_pattern = self.Export_MemoryAccess3D(read)

                        # we promote every local variable to a temporary:
                        try_add_transient(self.sdfg, name)

                        input_memlets[name + "_in"] = dace.Memlet.simple(name, access_pattern)

                    for write in stmt.writes:
                        name = self.id_resolver.GetName(write.id)
                        access_pattern = self.Export_MemoryAccess3D(write)

                        # we promote every local variable to a temporary:
                        try_add_transient(self.sdfg, name)

                        output_memlets[name + "_out"] = dace.Memlet.simple(name, access_pattern)

                    if stmt.code:
                        # Since we're in a sequential loop, we only need a map in i and j
                        map_range = dict(i="halo_size:I-halo_size", j="halo_size:J-halo_size")
                        state.add_mapped_tasklet(
                            str(stmt),
                            map_range,
                            input_memlets,
                            stmt.code,
                            output_memlets,
                            external_edges = True
                        )

                    # set the state to be the last one to connect to it
                    self.last_state_ = state

        if __debug__:
            print("loop order is: %s" % execution_order)

        if execution_order == ExecutionOrder.Forward_Loop.value:
            condition_expr = "k < %s" % interval.end
            increment_expr = "k + 1"
        elif execution_order == ExecutionOrder.Backward_Loop.value:
            condition_expr = "k > %s" % interval.end
            increment_expr = "k - 1"
        else:
            assert "wrong usage"
        
        _, _, last_state = self.sdfg.add_loop(
                prev_state,
                first_interval_state,
                None,
                "k",
                interval.begin,
                condition_expr,
                increment_expr,
                self.last_state_,
            )

    
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

    def Export_Stencil(self, stencil:Stencil):
        assert type(stencil) is Stencil
        
        for ms in stencil.multi_stages:
            self.Export_MultiStage(ms)

    def Export_Stencils(self, stencils: list):
        for s in stencils:
            self.Export_Stencil(s)
