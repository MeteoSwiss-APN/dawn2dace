/* DaCe AUTO-GENERATED FILE. DO NOT MODIFY */
#include <dace/dace.h>
                                                                                
                                                                                
void __program_IIRToSDFG_internal(double * __restrict__ data_in_1_t, double * __restrict__ data_in_2_t, double * __restrict__ data_out_t, int I, int J, int K, int halo_size)
{

    __state_IIRToSDFG_state_9:
    {
        #pragma omp parallel for
        for (auto k = 0; k < K; k += 1) {
            auto __data_in_2_S = dace::ArrayViewIn<double, 3, 1, dace::NA_RUNTIME> (data_in_2_t + (I * k), (I * (K + 1)), I, 1);
            auto *data_in_2_S = __data_in_2_S.ptr<1>();
            auto __data_out_S = dace::ArrayViewOut<double, 2, 1, dace::NA_RUNTIME> (data_out_t + (I * k), (I * (K + 1)), 1);
            auto *data_out_S = __data_out_S.ptr<1>();

            ///////////////////

            __state_ms_subsdfg10_state_11:
            {
                for (auto j = halo_size; j < (J - halo_size); j += 1) {
                    for (auto i = halo_size; i < (I - halo_size); i += 1) {
                        {
                            auto __data_in_2_input = dace::ArrayViewIn<double, 0, 1, 1> (data_in_2_S + (((I * j) * (K + 1)) + i));
                            dace::vec<double, 1> data_in_2_input = __data_in_2_input.val<1>();

                            auto __data_out = dace::ArrayViewOut<double, 0, 1, 1> (data_out_S + (((I * j) * (K + 1)) + i));
                            dace::vec<double, 1> data_out;

                            ///////////////////
                            // Tasklet code (statement)
                            data_out = data_in_2_input;
                            ///////////////////

                            __data_out.write(data_out);
                        }
                    }
                }
            }
            __state_exit_ms_subsdfg10_sdfg:;
            ///////////////////

        }
    }
    __state_IIRToSDFG_state_12:
    {
        #pragma omp parallel for
        for (auto k = 3; k < K; k += 1) {
            auto __data_in_1_S = dace::ArrayViewIn<double, 3, 1, dace::NA_RUNTIME> (data_in_1_t + (I * k), (I * (K + 1)), I, 1);
            auto *data_in_1_S = __data_in_1_S.ptr<1>();
            auto __data_out_S = dace::ArrayViewOut<double, 2, 1, dace::NA_RUNTIME> (data_out_t + (I * k), (I * (K + 1)), 1);
            auto *data_out_S = __data_out_S.ptr<1>();

            ///////////////////

            __state_ms_subsdfg13_state_14:
            {
                for (auto j = halo_size; j < (J - halo_size); j += 1) {
                    for (auto i = halo_size; i < (I - halo_size); i += 1) {
                        {
                            auto __data_in_1_input = dace::ArrayViewIn<double, 0, 1, 1> (data_in_1_S + (((I * j) * (K + 1)) + i));
                            dace::vec<double, 1> data_in_1_input = __data_in_1_input.val<1>();

                            auto __data_out = dace::ArrayViewOut<double, 0, 1, 1> (data_out_S + (((I * j) * (K + 1)) + i));
                            dace::vec<double, 1> data_out;

                            ///////////////////
                            // Tasklet code (statement)
                            data_out = data_in_1_input;
                            ///////////////////

                            __data_out.write(data_out);
                        }
                    }
                }
            }
            __state_exit_ms_subsdfg13_sdfg:;
            ///////////////////

        }
    }
    __state_exit_IIRToSDFG_sdfg:;
}

void __program_IIRToSDFG_internal(double * __restrict__ data_in_1_t, double * __restrict__ data_in_2_t, double * __restrict__ data_out_t, int I, int J, int K, int halo_size);
DACE_EXPORTED void __program_IIRToSDFG(double * __restrict__ data_in_1_t, double * __restrict__ data_in_2_t, double * __restrict__ data_out_t, int I, int J, int K, int halo_size)
{
    __program_IIRToSDFG_internal(data_in_1_t, data_in_2_t, data_out_t, I, J, K, halo_size);
}

DACE_EXPORTED int __dace_init(double * __restrict__ data_in_1_t, double * __restrict__ data_in_2_t, double * __restrict__ data_out_t, int I, int J, int K, int halo_size)
{
    int result = 0;

    return result;
}

DACE_EXPORTED void __dace_exit(double * __restrict__ data_in_1_t, double * __restrict__ data_in_2_t, double * __restrict__ data_out_t, int I, int J, int K, int halo_size)
{
}
