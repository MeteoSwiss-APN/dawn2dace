#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil brackets {
  storage input, output;
	
  Do {
    vertical_region(k_start, k_end) {
      output = 0.25 * (input + 7);
    }
  }
};