#include "gtclang_dsl_defs/math.hpp"
#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil mathfunctions {
  storage x, y;

  Do {
    vertical_region(k_start, k_end) {
      const double tmp = x;
      y = math::min(10.0, math::max(5.0, tmp));
    }
  }
};