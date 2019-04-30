/* DaCe AUTO-GENERATED FILE. DO NOT MODIFY */
#include <dace/dace.h>
                                                                                
                                                                                
void __program_IIRToSDFG_internal(double * __restrict__ data_in_2_t, double * __restrict__ data_out_t, double * __restrict__ data_in_1_t, int I, int J, int K, int halo_size)
{

    __state_IIRToSDFG_state_0:
    {
        // SuperSection start not emitted. Reasons: MISC
        #pragma omp parallel for
        for (auto i = halo_size; i < (I - halo_size); i += 1) {
            for (auto k = 0; k < K; k += 1) {
                for (auto j = halo_size; j < (J - halo_size); j += 1) {
                    {
                        auto __data_in_2 = dace::ArrayViewIn<double, 0, 1, 1> (data_in_2_t + ((((I * K) * j) + (I * k)) + i));
                        dace::vec<double, 1> data_in_2 = __data_in_2.val<1>();

                        auto __data_out = dace::ArrayViewOut<double, 0, 1, 1> (data_out_t + ((((I * K) * j) + (I * k)) + i));
                        dace::vec<double, 1> data_out;

                        ///////////////////
                        // Tasklet code (statement)
                        data_out = data_in_2;
                        ///////////////////

                        __data_out.write(data_out);
                    }
                }
            }
            // statement_map[i=halo_size:I - halo_size, k=0:K, j=halo_size:J - halo_size]
        }
    }
    __state_IIRToSDFG_state_1:
    {
        // SuperSection start not emitted. Reasons: MISC
        #pragma omp parallel for
        for (auto i = halo_size; i < (I - halo_size); i += 1) {
            for (auto k = 3; k < K; k += 1) {
                for (auto j = halo_size; j < (J - halo_size); j += 1) {
                    {
                        auto __data_in_1 = dace::ArrayViewIn<double, 0, 1, 1> (data_in_1_t + ((((I * K) * j) + (I * k)) + i));
                        dace::vec<double, 1> data_in_1 = __data_in_1.val<1>();

                        auto __data_out = dace::ArrayViewOut<double, 0, 1, 1> (data_out_t + ((((I * K) * j) + (I * k)) + i));
                        dace::vec<double, 1> data_out;

                        ///////////////////
                        // Tasklet code (statement)
                        data_out = data_in_1;
                        ///////////////////

                        __data_out.write(data_out);
                    }
                }
            }
            // statement_map[i=halo_size:I - halo_size, k=3:K, j=halo_size:J - halo_size]
        }
    }
    __state_exit_IIRToSDFG_sdfg:;
}

void __program_IIRToSDFG_internal(double * __restrict__ data_in_2_t, double * __restrict__ data_out_t, double * __restrict__ data_in_1_t, int I, int J, int K, int halo_size);
DACE_EXPORTED void __program_IIRToSDFG(double * __restrict__ data_in_2_t, double * __restrict__ data_out_t, double * __restrict__ data_in_1_t, int I, int J, int K, int halo_size)
{
    __program_IIRToSDFG_internal(data_in_2_t, data_out_t, data_in_1_t, I, J, K, halo_size);
}

DACE_EXPORTED int __dace_init(double * __restrict__ data_in_2_t, double * __restrict__ data_out_t, double * __restrict__ data_in_1_t, int I, int J, int K, int halo_size)
{
    int result = 0;

    return result;
}

DACE_EXPORTED void __dace_exit(double * __restrict__ data_in_2_t, double * __restrict__ data_out_t, double * __restrict__ data_in_1_t, int I, int J, int K, int halo_size)
{
}
