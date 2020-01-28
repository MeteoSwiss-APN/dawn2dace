#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil const_array {
  storage output, input;
  
  Do {	  
    vertical_region(k_start, k_end) {
      const double cf[5] = {-1.0, -2.0, 10.0, -3.0, -2.0};
      
      output = cf[0] * input[i-2]
             + cf[1] * input[i-1]
             + cf[2] * input
             + cf[3] * input[i+1]
             + cf[4] * input[i+2];
    }
  }
};