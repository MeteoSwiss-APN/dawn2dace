#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil test {
  storage a, b;
  Do {
    vertical_region(k_start, k_end) {
      // copy stencil
      a = b[i + 1, j - 1] + b[i - 1];
    }
  }
};