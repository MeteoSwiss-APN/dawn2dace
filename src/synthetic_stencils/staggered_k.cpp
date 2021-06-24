#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil staggered_k {
  storage mid_avg, data;

  Do {
    vertical_region(k_start, k_end) {
      mid_avg = data + data[k+1];
    }
  }
};