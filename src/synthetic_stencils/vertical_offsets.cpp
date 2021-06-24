#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil vertical_offsets {
  storage input, output;
	
  Do {
    vertical_region(k_start, k_start) {
      output = input[k+1];
    }
    vertical_region(k_start+1, k_end) {
      output = input[k-1];
    }
  }
};