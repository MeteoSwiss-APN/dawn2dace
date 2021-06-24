#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil ij_storage {
  storage output;
  storage_ij fill;

  Do {
    vertical_region(k_start, k_end) {
      output = fill;
    }
  }
};