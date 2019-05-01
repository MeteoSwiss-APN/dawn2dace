#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil test {
  storage in_field, out_field;
  Do {
    vertical_region(k_start, k_end) {
      // fill output
      out_field = 0.25 * (in_field + 7);
    }
  }
};