from itertools import permutations
import numpy as np
import reference
import dace
import sys
from dace.transformation.dataflow import *
from dace.transformation.optimizer import Optimizer
from dace.transformation.interstate import GPUTransformSDFG

# common_folder = '/scratch/snx3000/hdominic/dace/autotuning/'
common_folder = '/home/dominic/work/autotuning/'

def CreateSweep():
    sweep = []
    for domain_size in [(128,128,80),(256,256,80)]:
        for memory_layout in permutations(['k','i','j']): # 6
            memory_layout = ''.join(memory_layout)
            for loop_order in permutations(['k','i','j']): # 6
                loop_order = ''.join(loop_order)
                for block_size_i in [1,2,4,8,16,32,64,128]: # 8
                    for block_size_j in [1,2,4,8,16,32,64,128]: # 8
                        for block_size_k in [1,2,4,8,16]: # 5
                            if (block_size_i + 2) * (block_size_j + 2) * block_size_k <= 1024:
                                sweep.append((domain_size, memory_layout, loop_order, block_size_i, block_size_j, block_size_k))
    return sweep

def DataRelevant(run):
    return run[0], run[1]

def ProgramRelevant(run):
    return run[2], run[3], run[4], run[5]

def FullName(config):
    return '_'.join(''.join(str(x) for x in c) if isinstance(c, tuple) else str(c) for c in config)

def DataName(config):
    return '_'.join(''.join(str(x) for x in c) if isinstance(c, tuple) else str(c) for c in config)

def ProgramName(config):
    return '_'.join(''.join(str(x) for x in c) if isinstance(c, tuple) else str(c) for c in config)

def InVarName(config, index):
    return DataName(config) + f'_inVar{index}'

def OutVarName(config, index):
    return DataName(config) + f'_outVar{index}'

def CreateDataSet(sweep):
    data_set = []
    for s in sweep:
        tmp = DataRelevant(s)
        if tmp not in data_set:
            data_set.append(tmp)
    return data_set

def CreateProgramSet(sweep):
    program_set = []
    for s in sweep:
        tmp = ProgramRelevant(s)
        if tmp not in program_set:
            program_set.append(tmp)
    return program_set

if __name__ == "__main__":
    sweep = CreateSweep()
    data_set = CreateDataSet(sweep)
    program_set = CreateProgramSet(sweep)

    print(f'{len(sweep)} runs in this sweep')
    print(f'{len(data_set)} data sets in this sweep')
    print(f'{len(program_set)} programs in this sweep')
