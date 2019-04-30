/* DaCe AUTO-GENERATED FILE. DO NOT MODIFY */
#include <dace/dace.h>

void __program_IIRToSDFG_internal(double* __restrict__ data_in_t, double* __restrict__ data_out_t,
                                  int I, int J, int K) {

__state_IIRToSDFG_s1 : {
// SuperSection start not emitted. Reasons: MISC
#pragma omp parallel for
  for(auto j = 3; j < (J - 3); j += 1) {
    for(auto k = 0; k < K; k += 1) {
      for(auto i = 3; i < (I - 3); i += 1) {
        {
          auto __data_in =
              dace::ArrayViewIn<double, 0, 1, 1>(data_in_t + ((((I * K) * j) + (I * k)) + i));
          dace::vec<double, 1> data_in = __data_in.val<1>();

          auto __data_out =
              dace::ArrayViewOut<double, 0, 1, 1>(data_out_t + ((((I * K) * j) + (I * k)) + i));
          dace::vec<double, 1> data_out;

          ///////////////////
          // Tasklet code (stmt)
          data_out = data_in;
          ///////////////////

          __data_out.write(data_out);
        }
      }
    }
    // stmt_map[j=3:J - 3, k=0:K, i=3:I - 3]
  }
}
__state_exit_IIRToSDFG_sdfg:;
}

void __program_IIRToSDFG_internal(double* __restrict__ data_in_t, double* __restrict__ data_out_t,
                                  int I, int J, int K);
DACE_EXPORTED void __program_IIRToSDFG(double* __restrict__ data_in_t,
                                       double* __restrict__ data_out_t, int I, int J, int K) {
  __program_IIRToSDFG_internal(data_in_t, data_out_t, I, J, K);
}

DACE_EXPORTED int __dace_init(double* __restrict__ data_in_t, double* __restrict__ data_out_t,
                              int I, int J, int K) {
  int result = 0;

  return result;
}

DACE_EXPORTED void __dace_exit(double* __restrict__ data_in_t, double* __restrict__ data_out_t,
                               int I, int J, int K) {}
