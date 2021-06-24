#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil horizontal_offsets {
  storage a, b, c;
  Do {
    vertical_region(k_start, k_end) {
      a = b[i-1] + b[j+1] + b[i+1, j-1] + c[i-1];
    }
  }
};