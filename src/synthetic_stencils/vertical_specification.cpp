#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil vertical_spec_stencil {
  storage data_in_1, data_in_2, data_out;

  Do {
    vertical_region(k_start, k_end) {
      // specialization
      data_out = data_in_2;
    }
    vertical_region(k_start + 3, k_end) {
      // second specialization
      data_out = data_in_1;
    }
  }
};