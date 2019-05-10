/* DaCe AUTO-GENERATED FILE. DO NOT MODIFY */
#include <dace/dace.h>
                                                                                
                                                                                
void __program_IIRToSDFG_internal(double * __restrict__ in_field_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size)
{

    __state_IIRToSDFG_state_0:
    {
        double *__local_ee_30_t = new double DACE_ALIGN(64)[J * (K + 1) * I];
        // SuperSection start not emitted. Reasons: MISC
        #pragma omp parallel for
        for (auto i = halo_size; i < (I - halo_size); i += 1) {
            for (auto j = halo_size; j < (J - halo_size); j += 1) {
                for (auto k = 0; k < K; k += 1) {
                    {
                        auto __in_field_input = dace::ArrayViewIn<double, 0, 1, 1> (in_field_t + ((((I * j) * (K + 1)) + (I * k)) + i));
                        dace::vec<double, 1> in_field_input = __in_field_input.val<1>();

                        auto ____local_ee_30 = dace::ArrayViewOut<double, 0, 1, 1> (__local_ee_30_t + ((((I * j) * (K + 1)) + (I * k)) + i));
                        dace::vec<double, 1> __local_ee_30;

                        ///////////////////
                        // Tasklet code (statement)
                        __local_ee_30 = (in_field_input + 5);
                        ///////////////////

                        ____local_ee_30.write(__local_ee_30);
                    }
                }
            }
            // statement_map[i=halo_size:I - halo_size, j=halo_size:J - halo_size, k=0:K]
        }
        // SuperSection start not emitted. Reasons: MISC
        #pragma omp parallel for
        for (auto i = halo_size; i < (I - halo_size); i += 1) {
            for (auto j = halo_size; j < (J - halo_size); j += 1) {
                for (auto k = 0; k < K; k += 1) {
                    {
                        auto ____local_ee_30_input = dace::ArrayViewIn<double, 0, 1, 1> (__local_ee_30_t + ((((I * j) * (K + 1)) + (I * k)) + i));
                        dace::vec<double, 1> __local_ee_30_input = ____local_ee_30_input.val<1>();

                        auto __out_field = dace::ArrayViewOut<double, 0, 1, 1> (out_field_t + ((((I * j) * (K + 1)) + (I * k)) + i));
                        dace::vec<double, 1> out_field;

                        ///////////////////
                        // Tasklet code (statement)
                        out_field = __local_ee_30_input;
                        ///////////////////

                        __out_field.write(out_field);
                    }
                }
            }
            // statement_map[i=halo_size:I - halo_size, j=halo_size:J - halo_size, k=0:K]
        }
        delete[] __local_ee_30_t;
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
