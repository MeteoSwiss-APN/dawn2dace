#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil_function avg {
  offset off;
  storage in;

  Do { return 0.5 * (in[off] + in); }
};

stencil parametric_offsets {
  storage support, interpolation;

  Do {
    vertical_region(k_start, k_end) {
      interpolation = avg(i - 1, support) + avg(j + 1, support);
    }
  }
};