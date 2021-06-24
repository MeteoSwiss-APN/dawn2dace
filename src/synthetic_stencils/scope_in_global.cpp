#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

globals
{
  double global_var = 3.14;
};

stencil scope_in_global {
  storage input, output;
  
  Do {
    vertical_region(k_start, k_end) {
      output = input + global_var;
    }
  }
};