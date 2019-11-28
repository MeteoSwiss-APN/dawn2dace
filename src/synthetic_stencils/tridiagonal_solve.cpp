#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil tridiagonal_solve {
  storage d, a, b, c;

  Do {
    vertical_region(k_start, k_start) {
      c = c / b;
      d = d / b;
    }
    vertical_region(k_start + 1, k_end) {
      double m = 1.0 / (b - a * c[k - 1]);
      c = c * m;
      d = (d - a * d[k - 1]) * m;
    }
    vertical_region(k_end - 1, k_start) {
      d -= c * d[k + 1];
    }
  }
};
