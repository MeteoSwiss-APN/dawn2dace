#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil coriolis_stencil {
  storage u_tens, v_tens;
  storage u, v;
  storage_ij fc;

  Do() {
    vertical_region(k_start, k_end) {
      u_tens = u_tens + 0.25 * (fc * (v + v[i+1]) + fc[j-1] * (v[j-1] + v[i+1,j-1]));
      v_tens = v_tens - 0.25 * (fc * (u + u[j+1]) + fc[i-1] * (u[i-1] + u[i-1,j+1]));
    }
  }
};
