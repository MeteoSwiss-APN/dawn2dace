#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil_function d {
  offset off;
  storage data;

  double Do() { return data(off) - data; }
};

stencil delta {
  storage out, inp;

  Do {
    vertical_region(k_start + 1, k_end - 1) {
      out = 0.5 * d(k - 1, inp) + 2.0 * d(k + 1, inp);
    }
  }
};