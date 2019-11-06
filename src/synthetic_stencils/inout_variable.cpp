#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil test {
  storage a;
  void Do() {
    vertical_region(k_start, k_end) {
      // no offset doublebuffer not needed
      a = a + 7;
    }
  }
};