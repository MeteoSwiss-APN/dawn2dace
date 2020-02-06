#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil copy {
  storage output;

  Do {
    vertical_region(k_start, k_end) {
      output = 0;
    }
  }
};