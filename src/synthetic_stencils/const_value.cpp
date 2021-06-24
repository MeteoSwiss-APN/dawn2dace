#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil const_value {
  storage output, input;
  
  Do {	  
    vertical_region(k_start, k_end) {
      const double tmp = 10.0 / 5.0;
      
      output = input + tmp;
    }
  }
};