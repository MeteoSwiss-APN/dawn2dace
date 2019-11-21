#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil test {
  storage in_field, out_field;
  Do {
    vertical_region(k_start, k_start) {
      out_field = in_field[k+1];
    }
    vertical_region(k_start+1, k_end) {
      out_field = in_field[k-1];
    }
  }
};