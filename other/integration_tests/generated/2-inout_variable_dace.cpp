/* DaCe AUTO-GENERATED FILE. DO NOT MODIFY */
#include <dace/dace.h>
                                                                                
                                                                                
void __program_IIRToSDFG_internal(double * __restrict__ a_t, int I, int J, int K, int halo_size)
{

    __state_IIRToSDFG_state_5:
    {
        #pragma omp parallel for
        for (auto k = 0; k < K; k += 1) {
            auto __a_S = dace::ArrayViewOut<double, 2, 1, dace::NA_RUNTIME> (a_t + (I * k), (I * (K + 1)), 1);
            auto *a_S = __a_S.ptr<1>();

            ///////////////////

            __state_ms_subsdfg6_state_7:
            {
                for (auto j = halo_size; j < (J - halo_size); j += 1) {
                    for (auto i = halo_size; i < (I - halo_size); i += 1) {
                        {
                            auto __a_input = dace::ArrayViewIn<double, 0, 1, 1> (a_S + (((I * j) * (K + 1)) + i));
                            dace::vec<double, 1> a_input = __a_input.val<1>();

                            auto __a = dace::ArrayViewOut<double, 0, 1, 1> (a_S + (((I * j) * (K + 1)) + i));
                            dace::vec<double, 1> a;

                            ///////////////////
                            // Tasklet code (statement)
                            a = (a_input + 7);
                            ///////////////////

                            __a.write(a);
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

void __program_IIRToSDFG_internal(double * __restrict__ a_t, int I, int J, int K, int halo_size);
DACE_EXPORTED void __program_IIRToSDFG(double * __restrict__ a_t, int I, int J, int K, int halo_size)
{
    __program_IIRToSDFG_internal(a_t, I, J, K, halo_size);
}

DACE_EXPORTED int __dace_init(double * __restrict__ a_t, int I, int J, int K, int halo_size)
{
    int result = 0;

    return result;
}

DACE_EXPORTED void __dace_exit(double * __restrict__ a_t, int I, int J, int K, int halo_size)
{
}
