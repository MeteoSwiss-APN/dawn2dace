#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil vertical_specification_1 {
  storage input1, input2, output;

  Do {
    vertical_region(k_start, k_end-1) {
      output = input1;
    }
    vertical_region(k_start+1, k_end) {
      output = input2;
    }
  }
};