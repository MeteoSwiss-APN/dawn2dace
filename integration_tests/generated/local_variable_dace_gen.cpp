/* DaCe AUTO-GENERATED FILE. DO NOT MODIFY */
#include <dace/dace.h>
                                                                                
                                                                                
void __program_IIRToSDFG_internal(double * __restrict__ in_field_t, double * __restrict__ out_field_t, int I, int J, int K, int halo_size)
{

    __state_IIRToSDFG_state_0:
    {
        double *__local_ee_17_t = new double DACE_ALIGN(64)[J * K * I];
        // SuperSection start not emitted. Reasons: MISC
        #pragma omp parallel for
        for (auto k = 0; k < K; k += 1) {
            for (auto i = halo_size; i < (I - halo_size); i += 1) {
                for (auto j = halo_size; j < (J - halo_size); j += 1) {
                    {
                        auto __in_field = dace::ArrayViewIn<double, 0, 1, 1> (in_field_t + ((((I * K) * j) + (I * k)) + i));
                        dace::vec<double, 1> in_field = __in_field.val<1>();

                        auto ____local_ee_17 = dace::ArrayViewOut<double, 0, 1, 1> (__local_ee_17_t + ((((I * K) * j) + (I * k)) + i));
                        dace::vec<double, 1> __local_ee_17;

                        ///////////////////
                        // Tasklet code (statement)
                        __local_ee_17 = (in_field + 5);
                        ///////////////////

                        ____local_ee_17.write(__local_ee_17);
                    }
                }
            }
            // statement_map[k=0:K, i=halo_size:I - halo_size, j=halo_size:J - halo_size]
        }
        // SuperSection start not emitted. Reasons: MISC
        #pragma omp parallel for
        for (auto k = 0; k < K; k += 1) {
            for (auto i = halo_size; i < (I - halo_size); i += 1) {
                for (auto j = halo_size; j < (J - halo_size); j += 1) {
                    {
                        auto ____local_ee_17 = dace::ArrayViewIn<double, 0, 1, 1> (__local_ee_17_t + ((((I * K) * j) + (I * k)) + i));
                        dace::vec<double, 1> __local_ee_17 = ____local_ee_17.val<1>();

                        auto __out_field = dace::ArrayViewOut<double, 0, 1, 1> (out_field_t + ((((I * K) * j) + (I * k)) + i));
                        dace::vec<double, 1> out_field;

                        ///////////////////
                        // Tasklet code (statement)
                        out_field = __local_ee_17;
                        ///////////////////

                        __out_field.write(out_field);
                    }
                }
            }
            // statement_map[k=0:K, i=halo_size:I - halo_size, j=halo_size:J - halo_size]
        }
        delete[] __local_ee_17_t;
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
