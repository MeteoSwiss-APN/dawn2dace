from test_helpers import *
from dace.sdfg import SDFG
from dace.codegen import codegen, compiler
from dace.transformation.interstate import GPUTransformSDFG
from dace.transformation.dataflow import MapFusion

class Transcompiler():
    def test1_file_exists(self):
        self.assertIsNotNone(read_file(self.file_name + ".iir"))
 
    def test2_translates_to_sdfg(self):
        iir = read_file(self.file_name + ".iir")
        sdfg = dawn2dace.IIR_str_to_SDFG(iir)

        sdfg.save("gen/DyCore/Raw/" + self.file_name + ".sdfg")

    def test3_strict_trafo(self):
        sdfg = SDFG.from_file("gen/DyCore/Raw/" + self.file_name + ".sdfg")
        # Don't validate all the time, for performance reasons.
        sdfg.apply_strict_transformations(validate=False)
        sdfg.validate()
        sdfg.save("gen/DyCore/LibraryNodes/" + self.file_name + ".sdfg")

    def test4_expanded(self):
        sdfg = SDFG.from_file("gen/DyCore/Raw/" + self.file_name + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/DyCore/RawExpanded/" + self.file_name + ".sdfg")

        # Don't validate all the time, for performance reasons.
        sdfg.apply_strict_transformations(validate=False)
        sdfg.validate()
        sdfg.save("gen/DyCore/Expanded/" + self.file_name + ".sdfg")
        
        program_objects = codegen.generate_code(sdfg)
        compiler.generate_program_folder(sdfg, program_objects, "gen/" + self.file_name)

    # def test3_transforms_to_gpu(self):
    #     sdfg = SDFG.from_file("gen/" + self.file_name + ".sdfg")

    #     # Don't validate all the time, for performance reasons.
    #     sdfg.apply_transformations(GPUTransformSDFG, apply_once=True, validate=False)
    #     sdfg.validate()

    #     program_objects = codegen.generate_code(sdfg)
    #     compiler.generate_program_folder(sdfg, program_objects, "gen/" + self.file_name + "_gpu")

    #     sdfg.save("gen/" + self.file_name + "_gpu.sdfg")

    def test5_compiles(self):
        sdfg = SDFG.from_file("gen/DyCore/Expanded/" + self.file_name + ".sdfg")
        self.assertIsNotNone(sdfg.compile(optimizer=""))


class advection_pptp_0(Transcompiler, unittest.TestCase):
    file_name = "advection_pptp.0"

class cold_pools_0(Transcompiler, unittest.TestCase):
    file_name = "cold_pools.0"

class cold_pools_1(Transcompiler, unittest.TestCase):
    file_name = "cold_pools.1"

class convert_temp_0(Transcompiler, unittest.TestCase):
    file_name = "convert_temp.0"

class convert_temp_1(Transcompiler, unittest.TestCase):
    file_name = "convert_temp.1"

class coriolis_stencil_0(Transcompiler, unittest.TestCase):
    file_name = "coriolis_stencil.0"

class diab_latent_heat_0(Transcompiler, unittest.TestCase):
    file_name = "diab_latent_heat.0"

class diab_latent_heat_1(Transcompiler, unittest.TestCase):
    file_name = "diab_latent_heat.1"

class diab_latent_heat_2(Transcompiler, unittest.TestCase):
    file_name = "diab_latent_heat.2"

class fast_waves_Q_cond_0(Transcompiler, unittest.TestCase):
    file_name = "fast_waves_Q_cond.0"

class fast_waves_Q_cond_1(Transcompiler, unittest.TestCase):
    file_name = "fast_waves_Q_cond.1"

class fast_waves_sc_explicit_divergence_0(Transcompiler, unittest.TestCase):
    file_name = "fast_waves_sc_explicit_divergence.0"

class fast_waves_sc_lhs_0(Transcompiler, unittest.TestCase):
    file_name = "fast_waves_sc_lhs.0"

class fast_waves_sc_prepare_lhs_0(Transcompiler, unittest.TestCase):
    file_name = "fast_waves_sc_prepare_lhs.0"

class fast_waves_sc_rhs_0(Transcompiler, unittest.TestCase):
    file_name = "fast_waves_sc_rhs.0"

class fast_waves_sc_0(Transcompiler, unittest.TestCase):
    file_name = "fast_waves_sc.0"

class fast_waves_sc_uv_0(Transcompiler, unittest.TestCase):
    file_name = "fast_waves_sc_uv.0"

class fast_waves_sc_vertical_divergence_helper_0(Transcompiler, unittest.TestCase):
    file_name = "fast_waves_sc_vertical_divergence_helper.0"

class fast_waves_sc_wpptp_0(Transcompiler, unittest.TestCase):
    file_name = "fast_waves_sc_wpptp.0"

class horizontal_advection_0(Transcompiler, unittest.TestCase):
    file_name = "horizontal_advection.0"

class horizontal_advection_pptp_0(Transcompiler, unittest.TestCase):
    file_name = "horizontal_advection_pptp.0"

class horizontal_advection_uv_0(Transcompiler, unittest.TestCase):
    file_name = "horizontal_advection_uv.0"

class horizontal_advection_wwcon_0(Transcompiler, unittest.TestCase):
    file_name = "horizontal_advection_wwcon.0"

class horizontal_diffusion_0(Transcompiler, unittest.TestCase):
    file_name = "horizontal_diffusion.0"

class horizontal_diffusion_limiter_0(Transcompiler, unittest.TestCase):
    file_name = "horizontal_diffusion_limiter.0"

class horizontal_diffusion_smag_0(Transcompiler, unittest.TestCase):
    file_name = "horizontal_diffusion_smag.0"

class horizontal_diffusion_type2_full_0(Transcompiler, unittest.TestCase):
    file_name = "horizontal_diffusion_type2_full.0"

class horizontal_diffusion_type2_full_1(Transcompiler, unittest.TestCase):
    file_name = "horizontal_diffusion_type2_full.1"

class latent_heating_0(Transcompiler, unittest.TestCase):
    file_name = "latent_heating.0"

class latent_heating_1(Transcompiler, unittest.TestCase):
    file_name = "latent_heating.1"

class latent_heating_2(Transcompiler, unittest.TestCase):
    file_name = "latent_heating.2"

class relaxation_uv_tppw_0(Transcompiler, unittest.TestCase):
    file_name = "relaxation_uv_tppw.0"

class saturation_adjustment_0(Transcompiler, unittest.TestCase):
    file_name = "saturation_adjustment.0"

class vertical_advection_0(Transcompiler, unittest.TestCase):
    file_name = "vertical_advection.0"

class vertical_advection_1(Transcompiler, unittest.TestCase):
    file_name = "vertical_advection.1" 

class vertical_advection_pptp_0(Transcompiler, unittest.TestCase):
    file_name = "vertical_advection_pptp.0"

class vertical_advection_u_0(Transcompiler, unittest.TestCase):
    file_name = "vertical_advection_u.0"

class vertical_advection_uv_0(Transcompiler, unittest.TestCase):
    file_name = "vertical_advection_uv.0"

class vertical_diffusion_dqvdt_0(Transcompiler, unittest.TestCase):
    file_name = "vertical_diffusion_dqvdt.0"

class vertical_diffusion_prepare_step_0(Transcompiler, unittest.TestCase):
    file_name = "vertical_diffusion_prepare_step.0"

class vertical_diffusion_spptuvt_0(Transcompiler, unittest.TestCase):
    file_name = "vertical_diffusion_spptuvt.0"

class vertical_diffusion_T_0(Transcompiler, unittest.TestCase):
    file_name = "vertical_diffusion_T.0"

class vertical_diffusion_uvw_0(Transcompiler, unittest.TestCase):
    file_name = "vertical_diffusion_uvw.0"

class vertical_diffusion_w_0(Transcompiler, unittest.TestCase):
    file_name = "vertical_diffusion_w.0"


if __name__ == '__main__':
    unittest.main()
