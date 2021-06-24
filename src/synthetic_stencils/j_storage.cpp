#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil j_storage {
  storage output;
  storage_j fill;

  Do {
    vertical_region(k_start, k_end) {
      output = fill;
    }
  }
};