#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil_function laplacian {
  storage data;

  Do {
    return data[i + 1] + data[i - 1] + data[j + 1] + data[j - 1] - 4.0 * data;
  }
};

stencil laplace {
  storage output, input;

  Do {
    vertical_region(k_start, k_end) {
      output = laplacian(input);
    }
  }
};