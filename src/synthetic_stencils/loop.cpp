#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil vertical_loop {
  storage a;

  Do {
    vertical_region(k_start+1, k_end) {
      a += a[k-1];
    }
  }
};