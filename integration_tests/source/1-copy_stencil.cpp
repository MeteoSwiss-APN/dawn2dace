#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil copy_stencil {
  /* input fields */
  storage data_in;
  /* output fields */
  storage data_out;

  Do {
    vertical_region(k_start, k_end) {
      // Copy operator
      data_out = data_in;
    }
  }
};