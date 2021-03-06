from test_helpers import *
from dace.sdfg import SDFG
from dace.transformation.dataflow import MapFission, MapCollapse, MapFusion, MapExpansion, MapToForLoop, TrivialMapElimination, TrivialMapRangeElimination
from dace.transformation.interstate import InlineSDFG, StateFusion
from stencilflow.stencil.stencilfusion import StencilFusion
from stencilflow import canonicalize_sdfg
from dace.transformation.interstate import GPUTransformSDFG
from dace.codegen import codegen, compiler

# sdfg = SDFG.from_file("/home/dominic/work/dawn2dace/gen/DyCore/LibraryNodes/horizontal_diffusion.sdfg")
# canonicalize_sdfg(sdfg)
# sdfg.save("/home/dominic/work/dawn2dace/gen/HD_canonicalized.sdfg")

# # sdfg = SDFG.from_file("/home/dominic/work/dawn2dace/gen/HD_canonicalized.sdfg")
# sdfg.apply_transformations_repeated([StateFusion, InlineSDFG, StencilFusion])
# sdfg.save("/home/dominic/work/dawn2dace/gen/HD_canonicalized2.sdfg")

sdfg = SDFG.from_file("/home/dominic/work/dawn2dace/gen/DyCore/Expanded/coriolis_stencil.sdfg")
sdfg.apply_transformations_repeated([MapCollapse])
sdfg.apply_transformations_repeated([TrivialMapRangeElimination])
sdfg.save("/home/dominic/work/C-cpu.sdfg")
sdfg.apply_transformations(GPUTransformSDFG, options={'strict_transform': False})
for state in sdfg.nodes():
    state.instrument = dace.InstrumentationType.GPU_Events
sdfg.save("/home/dominic/work/C-gpu.sdfg")

# sdfg = SDFG.from_file("/home/dominic/work/dawn2dace/gen/HD_expanded.sdfg")
# sdfg.apply_transformations(GPUTransformSDFG, validate=False)
# sdfg.validate()
# sdfg.save("/home/dominic/work/dawn2dace/gen/HD_gpu.sdfg")

# sdfg = SDFG.from_file("/home/dominic/work/dawn2dace/gen/HD_gpu.sdfg")
# program_objects = codegen.generate_code(sdfg)
# compiler.generate_program_folder(sdfg, program_objects, "/home/dominic/work/dawn2dace/gen/HD")