#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil copy_stencil {
  storage original, copy;

  Do {
    vertical_region(k_start, k_end) {
      copy = original;
    }
  }
};