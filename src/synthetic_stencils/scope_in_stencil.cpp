#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil scope_in_stencil {
  storage input, output;
  
  var tmp;
  Do {
    vertical_region(k_start, k_end) {
      tmp = input + 5;
      output = tmp;
    }
  }
};