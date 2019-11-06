#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil test {
  storage in_field, out_field;
  Do {
    vertical_region(k_start, k_start) {
      // initialize bottom
      out_field = in_field;
    }
    vertical_region(k_start + 1, k_end) {
      // shift up
      out_field = in_field[k - 1];
    }
  }
};