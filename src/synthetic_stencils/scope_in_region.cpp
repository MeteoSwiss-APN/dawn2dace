#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil scope_in_region {
  storage input, output;
  
  Do {
    vertical_region(k_start, k_end) {
      double tmp = input + 5;
      output = tmp;
    }
  }
};