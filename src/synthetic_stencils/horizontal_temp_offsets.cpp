#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil horizontal_temp_offset {
  storage output, input;
  var tmp;

  Do {
    vertical_region(k_start, k_end) {
      tmp = input;
      output = tmp[i-1];
    }
  }
};