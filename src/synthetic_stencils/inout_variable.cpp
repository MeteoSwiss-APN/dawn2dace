#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil inout {
  storage a;
  
  void Do() {
    vertical_region(k_start, k_end) {
      // no offset, thus doublebuffer not needed.
      a = a + 7;
    }
  }
};