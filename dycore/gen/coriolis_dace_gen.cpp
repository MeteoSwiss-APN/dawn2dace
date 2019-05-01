/* DaCe AUTO-GENERATED FILE. DO NOT MODIFY */
#include <dace/dace.h>
                                                                                
                                                                                
void __program_IIRToSDFG_internal(double * __restrict__ fc_t, double * __restrict__ u_tens_t, double * __restrict__ v_nnow_t, double * __restrict__ v_tens_t, double * __restrict__ u_nnow_t, int I, int J, int K, int halo_size)
{

    __state_IIRToSDFG_state_0:
    {
        #pragma omp parallel sections                                           
        {                                                                       
            #pragma omp section                                                 
            {                                                                   
                // SuperSection start not emitted. Reasons: CONTAINER_IS_PARALLEL,MISC
                #pragma omp parallel for
                for (auto k = 0; k < K; k += 1) {
                    for (auto j = halo_size; j < (J - halo_size); j += 1) {
                        for (auto i = halo_size; i < (I - halo_size); i += 1) {
                            {
                                auto __u_tens_input = dace::ArrayViewIn<double, 0, 1, 1> (u_tens_t + ((((I * K) * j) + (I * k)) + i));
                                dace::vec<double, 1> u_tens_input = __u_tens_input.val<1>();
                                auto __v_nnow = dace::ArrayViewIn<double, 2, 1, dace::NA_RUNTIME> (v_nnow_t + ((((I * K) * (j - 1)) + (I * k)) + i), (I * K), 1);
                                auto *v_nnow = __v_nnow.ptr<1>();
                                auto __fc = dace::ArrayViewIn<double, 1, 1, dace::NA_RUNTIME> (fc_t + ((((I * K) * (j - 1)) + (I * k)) + i), (I * K));
                                auto *fc = __fc.ptr<1>();

                                auto __u_tens = dace::ArrayViewOut<double, 0, 1, 1> (u_tens_t + ((((I * K) * j) + (I * k)) + i));
                                dace::vec<double, 1> u_tens;

                                ///////////////////
                                // Tasklet code (statement)
                                u_tens = u_tens_input;
                                u_tens += (0.25 * ((__fc(1) * (__v_nnow(1, 0) + __v_nnow(1, 1))) + (__fc(0) * (__v_nnow(0, 0) + __v_nnow(0, 1)))));
                                ///////////////////

                                __u_tens.write(u_tens);
                            }
                        }
                    }
                    // statement_map[k=0:K, j=halo_size:J - halo_size, i=halo_size:I - halo_size]
                }
            } // End omp section                                                
            #pragma omp section                                                 
            {                                                                   
                // SuperSection start not emitted. Reasons: CONTAINER_IS_PARALLEL,MISC
                #pragma omp parallel for
                for (auto k = 0; k < K; k += 1) {
                    for (auto j = halo_size; j < (J - halo_size); j += 1) {
                        for (auto i = halo_size; i < (I - halo_size); i += 1) {
                            {
                                auto __u_nnow = dace::ArrayViewIn<double, 2, 1, dace::NA_RUNTIME> (u_nnow_t + (((((I * K) * j) + (I * k)) + i) - 1), (I * K), 1);
                                auto *u_nnow = __u_nnow.ptr<1>();
                                auto __fc = dace::ArrayViewIn<double, 1, 1, dace::NA_RUNTIME> (fc_t + (((((I * K) * j) + (I * k)) + i) - 1), 1);
                                auto *fc = __fc.ptr<1>();
                                auto __v_tens_input = dace::ArrayViewIn<double, 0, 1, 1> (v_tens_t + ((((I * K) * j) + (I * k)) + i));
                                dace::vec<double, 1> v_tens_input = __v_tens_input.val<1>();

                                auto __v_tens = dace::ArrayViewOut<double, 0, 1, 1> (v_tens_t + ((((I * K) * j) + (I * k)) + i));
                                dace::vec<double, 1> v_tens;

                                ///////////////////
                                // Tasklet code (statement)
                                v_tens = v_tens_input;
                                v_tens -= (0.25 * ((__fc(1) * (__u_nnow(0, 1) + __u_nnow(1, 1))) + (__fc(0) * (__u_nnow(0, 0) + __u_nnow(1, 0)))));
                                ///////////////////

                                __v_tens.write(v_tens);
                            }
                        }
                    }
                    // statement_map[k=0:K, j=halo_size:J - halo_size, i=halo_size:I - halo_size]
                }
            } // End omp section                                                
        } // End omp sections                                                   
    }
    __state_exit_IIRToSDFG_sdfg:;
}

void __program_IIRToSDFG_internal(double * __restrict__ fc_t, double * __restrict__ u_tens_t, double * __restrict__ v_nnow_t, double * __restrict__ v_tens_t, double * __restrict__ u_nnow_t, int I, int J, int K, int halo_size);
DACE_EXPORTED void __program_IIRToSDFG(double * __restrict__ fc_t, double * __restrict__ u_tens_t, double * __restrict__ v_nnow_t, double * __restrict__ v_tens_t, double * __restrict__ u_nnow_t, int I, int J, int K, int halo_size)
{
    __program_IIRToSDFG_internal(fc_t, u_tens_t, v_nnow_t, v_tens_t, u_nnow_t, I, J, K, halo_size);
}

DACE_EXPORTED int __dace_init(double * __restrict__ fc_t, double * __restrict__ u_tens_t, double * __restrict__ v_nnow_t, double * __restrict__ v_tens_t, double * __restrict__ u_nnow_t, int I, int J, int K, int halo_size)
{
    int result = 0;

    return result;
}

DACE_EXPORTED void __dace_exit(double * __restrict__ fc_t, double * __restrict__ u_tens_t, double * __restrict__ v_nnow_t, double * __restrict__ v_tens_t, double * __restrict__ u_nnow_t, int I, int J, int K, int halo_size)
{
}
