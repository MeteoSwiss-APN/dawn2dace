#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil duplicate {
  storage original, copy;

  Do {
    vertical_region(k_start, k_end) {
      copy = original;
    }
  }
};