#include "gtclang_dsl_defs/math.hpp"
#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil mathfunctions {
  storage x, y;

  Do {
    vertical_region(k_start, k_end) {
      y = math::min(5.0, math::max(10.0, x));
    }
  }
};