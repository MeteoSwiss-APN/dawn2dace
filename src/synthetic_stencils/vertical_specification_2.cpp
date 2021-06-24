#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil vertical_specification_2 {
  storage input1, input2, output;

  Do {
    vertical_region(k_start+1, k_end) {
      output = input2;
    }
    vertical_region(k_start, k_end-1) {
      output = input1;
    }
  }
};