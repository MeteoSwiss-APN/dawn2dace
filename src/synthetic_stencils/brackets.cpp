#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil brackets {
  storage input, output;
	
  Do {
    vertical_region(k_start, k_end) {
      output = 0.25 * (input + 7);
    }
  }
};