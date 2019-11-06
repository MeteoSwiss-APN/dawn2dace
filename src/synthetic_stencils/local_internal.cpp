#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil test {
  storage in_field, out_field;
  Do {
    vertical_region(k_start, k_end) {
      double ee = in_field + 5;
      out_field = ee;
    }
  }
};