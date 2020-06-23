#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

stencil_function laplacian {
  storage data;

  Do {
    return data[i + 1] + data[i - 1] + data[j + 1] + data[j - 1] - 4.0 * data;
  }
};

stencil_function diffusive_flux_x {
  storage lap, data;

  Do {
    const double flx = lap[i + 1] - lap;
    return (flx * (data[i + 1] - data)) > 0.0 ? 0.0 : flx;
  }
};

/// Type2 - Diffusion
stencil diffusion {
  storage output, input;
  var lap;

  Do {
    vertical_region(k_start, k_end) {
      lap = laplacian(input);
      output = diffusive_flux_x(lap, input) - diffusive_flux_x(lap[i - 1], input[i - 1]);
    }
  }
};