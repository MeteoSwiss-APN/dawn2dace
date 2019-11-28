#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

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