/* DaCe AUTO-GENERATED FILE. DO NOT MODIFY */
#include <dace/dace.h>
                                                                                
                                                                                
void __program_IIRToSDFG_internal(double * __restrict__ in_field_t, float global2_t, float testglobal_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size)
{

    __state_IIRToSDFG_state_0:
    {
        // SuperSection start not emitted. Reasons: MISC
        #pragma omp parallel for
        for (auto k = 0; k < K; k += 1) {
            for (auto j = halo_size; j < (J - halo_size); j += 1) {
                for (auto i = halo_size; i < (I - halo_size); i += 1) {
                    {
                        auto __testglobal_input = dace::ArrayViewIn<float, 0, 1, 1> (&testglobal_t);
                        dace::vec<float, 1> testglobal_input = __testglobal_input.val<1>();
                        auto __global2_input = dace::ArrayViewIn<float, 0, 1, 1> (&global2_t);
                        dace::vec<float, 1> global2_input = __global2_input.val<1>();
                        auto __in_field_input = dace::ArrayViewIn<double, 0, 1, 1> (in_field_t + ((((I * j) * (K + 1)) + (I * k)) + i));
                        dace::vec<double, 1> in_field_input = __in_field_input.val<1>();

                        auto __out_field = dace::ArrayViewOut<double, 0, 1, 1> (out_field_t + ((((I * j) * (K + 1)) + (I * k)) + i));
                        dace::vec<double, 1> out_field;

                        ///////////////////
                        // Tasklet code (statement)
                        out_field = ((in_field_input + testglobal_input) + global2_input);
                        ///////////////////

                        __out_field.write(out_field);
                    }
                }
            }
            // statement_map[k=0:K, j=halo_size:J - halo_size, i=halo_size:I - halo_size]
        }
    }
    __state_exit_IIRToSDFG_sdfg:;
}

void __program_IIRToSDFG_internal(double * __restrict__ in_field_t, float global2_t, float testglobal_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size);
DACE_EXPORTED void __program_IIRToSDFG(double * __restrict__ in_field_t, float global2_t, float testglobal_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size)
{
    __program_IIRToSDFG_internal(in_field_t, global2_t, testglobal_t, out_field_t, I, J, K, halo_size);
}

DACE_EXPORTED int __dace_init(double * __restrict__ in_field_t, float global2_t, float testglobal_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size)
{
    int result = 0;

    return result;
}

DACE_EXPORTED void __dace_exit(double * __restrict__ in_field_t, float global2_t, float testglobal_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size)
{
}
