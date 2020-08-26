from test_helpers import *
from dace.sdfg import SDFG
from dace.codegen import codegen, compiler
from dace.transformation.dataflow import MapFission, MapCollapse, MapFusion
from dace.transformation.interstate import InlineSDFG, StateFusion, GPUTransformSDFG
from stencilflow.stencil.stencilfusion import StencilFusion
from stencilflow import canonicalize_sdfg

class Transcompiler():
    def test1_file_exists(self):
        self.assertIsNotNone(read_file(self.__class__.__name__ + ".iir"))
 
    def test2_translates_to_sdfg(self):
        iir = read_file(self.__class__.__name__ + ".iir")
        sdfg = dawn2dace.IIR_str_to_SDFG(iir)

        sdfg.save("gen/DyCore/Raw/" + self.__class__.__name__ + ".sdfg")

    def test3_strict_trafo(self):
        sdfg = SDFG.from_file("gen/DyCore/Raw/" + self.__class__.__name__ + ".sdfg")
        # Don't validate all the time, for performance reasons.
        sdfg.apply_strict_transformations(validate=False)
        sdfg.validate()
        sdfg.save("gen/DyCore/LibraryNodes/" + self.__class__.__name__ + ".sdfg")

    def test4_expanded(self):
        sdfg = SDFG.from_file("gen/DyCore/Raw/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/DyCore/RawExpanded/" + self.__class__.__name__ + ".sdfg")

        # Don't validate all the time, for performance reasons.
        sdfg.apply_strict_transformations(validate=False)
        sdfg.validate()
        sdfg.save("gen/DyCore/Expanded/" + self.__class__.__name__ + ".sdfg")

    def test5_compiles(self):
        sdfg = SDFG.from_file("gen/DyCore/Expanded/" + self.__class__.__name__ + ".sdfg")
        program_objects = codegen.generate_code(sdfg)
        compiler.generate_program_folder(sdfg, program_objects, "gen/" + self.__class__.__name__)
        self.assertIsNotNone(sdfg.compile())

    # def test6_transforms_to_gpu(self):
    #     sdfg = SDFG.from_file("gen/DyCore/LibraryNodes/" + self.__class__.__name__ + ".sdfg")

    #     canonicalize_sdfg(sdfg)
    #     sdfg.save("gen/" + self.__class__.__name__ + "_canonicalize.sdfg")
        
    #     sdfg.apply_transformations_repeated([StateFusion, InlineSDFG, StencilFusion])
    #     sdfg.save("gen/" + self.__class__.__name__ + "_fused.sdfg")
    #     sdfg = SDFG.from_file("gen/" + self.__class__.__name__ + "_fused.sdfg")
    #     sdfg.expand_library_nodes()
    #     sdfg.apply_transformations_repeated([InlineSDFG])
    #     sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
    #     sdfg = SDFG.from_file("gen/" + self.__class__.__name__ + "_expanded.sdfg")
    #     sdfg.apply_transformations(GPUTransformSDFG, validate=False)
    #     sdfg.validate()
    #     sdfg.save("gen/DyCore/GPU/" + self.__class__.__name__ + ".sdfg")
    #     program_objects = codegen.generate_code(sdfg)
    #     compiler.generate_program_folder(sdfg, program_objects, "gen/" + self.__class__.__name__)


class advection_pptp(Transcompiler, unittest.TestCase):
    pass

class ConvertTemperature_DoT(Transcompiler, unittest.TestCase):
    pass

class ConvertTemperature_DoTP(Transcompiler, unittest.TestCase):
    pass

class coriolis_stencil(Transcompiler, unittest.TestCase):
    pass

class DiabLatentHeat_pStencilAdd(Transcompiler, unittest.TestCase):
    pass

class DiabLatentHeat_pStencilInit(Transcompiler, unittest.TestCase):
    pass

class DiabLatentHeat_pStencilSub(Transcompiler, unittest.TestCase):
    pass

class DoGsLheatingAdd(Transcompiler, unittest.TestCase):
    pass

class DoGsLheatingInc(Transcompiler, unittest.TestCase):
    pass

class fast_waves_explicit_divergence(Transcompiler, unittest.TestCase):
    pass

class fast_waves(Transcompiler, unittest.TestCase):
    pass

class fast_waves_lhs(Transcompiler, unittest.TestCase):
    pass

class fast_waves_prepare_lhs(Transcompiler, unittest.TestCase):
    pass

class fast_waves_rhs(Transcompiler, unittest.TestCase):
    pass

class FastWavesSCQCond(Transcompiler, unittest.TestCase):
    pass

class FastWavesSCQCond_QC(Transcompiler, unittest.TestCase):
    pass

class fast_waves_uv(Transcompiler, unittest.TestCase):
    pass

class fast_waves_vertical_divergence_helper(Transcompiler, unittest.TestCase):
    pass

class fast_waves_wpptp(Transcompiler, unittest.TestCase):
    pass

class horizontal_advection(Transcompiler, unittest.TestCase):
    pass

class horizontal_advection_pptp(Transcompiler, unittest.TestCase):
    pass

class horizontal_advection_uv(Transcompiler, unittest.TestCase):
    pass

class horizontal_advection_wwcon(Transcompiler, unittest.TestCase):
    pass

class HorizontalDiffusion2Limiter(Transcompiler, unittest.TestCase):
    pass

class HorizontalDiffusionColdPoolTPCopyStencil(Transcompiler, unittest.TestCase):
    pass

class HorizontalDiffusionColdPoolTP(Transcompiler, unittest.TestCase):
    pass

class horizontal_diffusion(Transcompiler, unittest.TestCase):
    pass

class horizontal_diffusion_smag(Transcompiler, unittest.TestCase):
    pass

class horizontal_diffusion_type2(Transcompiler, unittest.TestCase):
    pass

class pStencilSetTtLheat_(Transcompiler, unittest.TestCase):
    pass

class RelaxationUVTPPW(Transcompiler, unittest.TestCase):
    pass

class SaturationAdjustment(Transcompiler, unittest.TestCase):
    pass

class type2(Transcompiler, unittest.TestCase):
    pass

class vertical_advection(Transcompiler, unittest.TestCase):
    pass

class vertical_advection_pptp(Transcompiler, unittest.TestCase):
    pass

class vertical_advection_u(Transcompiler, unittest.TestCase):
    pass

class vertical_advection_uv(Transcompiler, unittest.TestCase):
    pass

class vertical_advection_uvw(Transcompiler, unittest.TestCase):
    pass

class verticalDiffusionDqvdt(Transcompiler, unittest.TestCase):
    pass

class vertical_diffusion_prepare_step(Transcompiler, unittest.TestCase):
    pass

class verticalDiffusionSPPTUVT(Transcompiler, unittest.TestCase):
    pass

class verticalDiffusionT(Transcompiler, unittest.TestCase):
    pass

class verticalDiffusionUVW(Transcompiler, unittest.TestCase):
    pass

class verticalDiffusionW(Transcompiler, unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
