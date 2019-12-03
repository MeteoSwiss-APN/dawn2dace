#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

globals
{
  double global_var = 3.14;
};

stencil scope_in_region {
  storage input, output;
  
  Do {
    vertical_region(k_start, k_end) {
      output = input + global_var;
    }
  }
};