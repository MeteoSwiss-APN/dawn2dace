#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil inout_variable {
  storage a;
  
  Do() {
    vertical_region(k_start, k_end) {
      // no offset, thus doublebuffer not needed.
      a = a + 7;
    }
  }
};