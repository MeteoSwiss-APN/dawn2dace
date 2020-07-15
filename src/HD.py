from test_helpers import *
from dace.sdfg import SDFG
from dace.transformation.dataflow import MapFission, MapCollapse, MapFusion
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

sdfg = SDFG.from_file("/home/dominic/work/dawn2dace/gen/HD_canonicalized2.sdfg")
sdfg.expand_library_nodes()
sdfg.apply_transformations_repeated([StateFusion, InlineSDFG, StencilFusion])
sdfg.save("/home/dominic/work/dawn2dace/gen/HD_canonicalized_expanded.sdfg")

# sdfg = SDFG.from_file("/home/dominic/work/dawn2dace/gen/HD_expanded.sdfg")
# sdfg.apply_transformations(GPUTransformSDFG, validate=False)
# sdfg.validate()
# sdfg.save("/home/dominic/work/dawn2dace/gen/HD_gpu.sdfg")

# sdfg = SDFG.from_file("/home/dominic/work/dawn2dace/gen/HD_gpu.sdfg")
# program_objects = codegen.generate_code(sdfg)
# compiler.generate_program_folder(sdfg, program_objects, "/home/dominic/work/dawn2dace/gen/HD")