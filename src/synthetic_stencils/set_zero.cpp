#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil set_zero {
  storage output;

  Do {
    vertical_region(k_start, k_end) {
      output = 0;
    }
  }
};