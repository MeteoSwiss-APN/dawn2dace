/* DaCe AUTO-GENERATED FILE. DO NOT MODIFY */
#include <dace/dace.h>
                                                                                
                                                                                
void __program_IIRToSDFG_internal(double * __restrict__ in_field_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size)
{

    __state_IIRToSDFG_state_5:
    {
        #pragma omp parallel for
        for (auto k = 0; k < K; k += 1) {
            auto __in_field_S = dace::ArrayViewIn<double, 3, 1, dace::NA_RUNTIME> (in_field_t + (I * k), (I * (K + 1)), I, 1);
            auto *in_field_S = __in_field_S.ptr<1>();
            auto __out_field_S = dace::ArrayViewOut<double, 2, 1, dace::NA_RUNTIME> (out_field_t + (I * k), (I * (K + 1)), 1);
            auto *out_field_S = __out_field_S.ptr<1>();

            ///////////////////

            __state_ms_subsdfg6_state_7:
            {
                for (auto j = halo_size; j < (J - halo_size); j += 1) {
                    for (auto i = halo_size; i < (I - halo_size); i += 1) {
                        {
                            auto __in_field_input = dace::ArrayViewIn<double, 0, 1, 1> (in_field_S + (((I * j) * (K + 1)) + i));
                            dace::vec<double, 1> in_field_input = __in_field_input.val<1>();

                            auto __out_field = dace::ArrayViewOut<double, 0, 1, 1> (out_field_S + (((I * j) * (K + 1)) + i));
                            dace::vec<double, 1> out_field;

                            ///////////////////
                            // Tasklet code (statement)
                            out_field = (0.25 * (in_field_input + 7));
                            ///////////////////

                            __out_field.write(out_field);
                        }
                    }
                }
            }
            __state_exit_ms_subsdfg6_sdfg:;
            ///////////////////

        }
    }
    __state_exit_IIRToSDFG_sdfg:;
}

void __program_IIRToSDFG_internal(double * __restrict__ in_field_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size);
DACE_EXPORTED void __program_IIRToSDFG(double * __restrict__ in_field_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size)
{
    __program_IIRToSDFG_internal(in_field_t, out_field_t, I, J, K, halo_size);
}

DACE_EXPORTED int __dace_init(double * __restrict__ in_field_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size)
{
    int result = 0;

    return result;
}

DACE_EXPORTED void __dace_exit(double * __restrict__ in_field_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size)
{
}
