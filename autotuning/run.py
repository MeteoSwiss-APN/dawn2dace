from itertools import permutations
from sweep import *
import numpy as np
import reference
import dace
import sys

def CreateProgam(program_config):
    loop_order, block_size_i, block_size_j, block_size_k = program_config
    loop_order = [lo.replace('i','x').replace('j','y') for lo in loop_order]
    tile_sizes = [block_size_k, block_size_i, block_size_j]

    sdfg = dace.sdfg.SDFG.from_file(common_folder + 'smag-HoriFused.sdfg')

    # BufferTiling
    for match in Optimizer(sdfg, inplace=True).get_pattern_matches(patterns=[BufferTiling]):
        match.tile_sizes = tile_sizes
        match.apply_pattern(sdfg)
        break

    # #OTF Tiling
    # for match in Optimizer(sdfg, inplace=True).get_pattern_matches(patterns=[MapTiling]):
    #     graph = sdfg.nodes()[match.state_id]
    #     map_entry = graph.nodes()[match.subgraph[match._map_entry]]
    #     if map_entry.map.label == 'BufferTiling':
    #         match.tile_sizes = tile_sizes
    #         match.apply_pattern(sdfg)
    #         map_entry.map.label = 'BufferTiling2'
    #         map_entry.schedule = dace.ScheduleType.GPU_ThreadBlock
    #         break

    # MapDimShuffle
    params1 = [lo for ts,lo in zip(tile_sizes, loop_order) if ts != 1]
    params2 = [f'tile_{lo}' for lo in loop_order]
    for params in [params1, params2, loop_order]:
        for match in Optimizer(sdfg, inplace=True).get_pattern_matches(patterns=[MapDimShuffle]):
            graph = sdfg.nodes()[match.state_id]
            map_entry = graph.nodes()[match.subgraph[match._map_entry]]
            if set(map_entry.map.params) == set(params):
                match.parameters = params
                match.apply_pattern(sdfg)

    for arr in sdfg.arrays.values():
        arr.dtype = dace.float32

    # for state in sdfg.nodes():
    #     state.instrument = dace.InstrumentationType.Timer

    sdfg.apply_transformations(GPUTransformSDFG, options={'strict_transform':False, 'sequential_innermaps':False}, validate=False)

    for state in sdfg.nodes():
        if state.name.startswith('ms_state'):
            state.instrument = dace.InstrumentationType.GPU_Events

    for state in sdfg.nodes():
        for node in state.nodes():
            if isinstance(node, dace.sdfg.nodes.MapEntry):
                if node.label =='outer_fused':
                    node.schedule = dace.ScheduleType.Unrolled

    for state in sdfg.nodes():
        for node in state.nodes():
            if isinstance(node, dace.sdfg.nodes.MapEntry):
                if all(not p.startswith('tile_') for p in node.map.params):
                    node.schedule = dace.ScheduleType.GPU_ThreadBlock

    for name, arr in sdfg.arrays.items():
        if name.startswith('__s0'):
            arr.storage = dace.StorageType.GPU_Shared

    sdfg.transformation_hist = []
    sdfg.name = ProgramName(program_config)
    sdfg.save(common_folder + f'smag-gpu_{sdfg.name}.sdfg')
    return sdfg

def run(sdfg, config):
    num_input_vars = 6
    num_output_vars = 2
    input_vars = []
    output_vars = []

    data_config = DataRelevant(config)

    # load the input data
    # for index in range(num_input_vars):
    #     file_name = common_folder + InVarName(data_config, index) + '.npy'
    #     input_vars.append(np.load(file_name))
    u_in, v_in, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0 = reference.CreateInputData(*data_config)

    domain_size, memory_layout, *_ = config

    I,J,K = domain_size
    memory_sizes = [I,J,K+1]
    dim = reference.Dimensions(domain_sizes=domain_size, memory_sizes=memory_sizes, memory_layout=memory_layout, halo=4)
    u_out_dace = reference.Zeros(dim.ijk)
    v_out_dace = reference.Zeros(dim.ijk)

    sdfg(
        acrlat0 = acrlat0,
        crlavo = crlavo,
        crlavu = crlavu,
        crlato = crlato,
        crlatu = crlatu,
        hdmaskvel = hdmask,
        u_out = u_out_dace,
        u_in = u_in,
        v_out = v_out_dace,
        v_in = v_in,
        **dim.ProgramArguments())

    with open(common_folder + f'log_{FullName(config)}.txt', 'w') as f:
        original_stdout = sys.stdout
        sys.stdout = f
        print(f'{config} {sdfg.get_latest_report().durations}')

        if (config[0] == (128,128,80)):
            # load the reference output data
            for index in range(num_output_vars):
                file_name = common_folder + OutVarName(data_config, index) + '.npy'
                output_vars.append(np.load(file_name))
            u_out, v_out = output_vars
            reference.assertIsClose(u_out, u_out_dace, 'u', dim)
            reference.assertIsClose(v_out, v_out_dace, 'v', dim)

        sys.stdout = original_stdout


def main():
    sweep_index = int(sys.argv[1])
    
    sweep = CreateSweep()
    data_set = CreateDataSet(sweep)
    program_set = CreateProgramSet(sweep)

    # run all configs for one program
    if (sweep_index >= len(program_set)):
        return
    program_config = program_set[sweep_index]
    sdfg = CreateProgam(program_config)
    for s in sweep:
        if ProgramRelevant(s) == program_config:
            run(sdfg, s)

if __name__ == "__main__":
    main()