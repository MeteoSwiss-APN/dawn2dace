#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

// Thomas algorithm - forward sweep
stencil_function tridiagonal_forward {
  storage acol, bcol, ccol, dcol;

  Do(k_from = k_start, k_to = k_start) {
    const double divided = 1.0 / bcol;
    ccol = ccol * divided;
    dcol = dcol * divided;
  }

  Do(k_from = k_start + 1, k_to = k_end - 1) {
    const double divided = 1.0 / (bcol - (ccol[k - 1] * acol));
    ccol = ccol * divided;
    dcol = dcol - (dcol[k - 1] * acol) * divided;
  }

  Do(k_from = k_end, k_to = k_end) {
    const double divided = 1.0 / (bcol - (ccol[k - 1] * acol));
    dcol = (dcol - (dcol[k - 1] * acol)) * divided;
  }
};

// Thomas algorithm - backward sweep
stencil_function tridiagonal_backward {
  storage ccol, dcol, datacol;

  Do(k_from = k_end, k_to = k_end) { datacol = dcol; }

  Do(k_from = k_start, k_to = k_end - 1) { datacol = dcol - (ccol * datacol[k + 1]); }
};

stencil thomas {
  storage acol, bcol, ccol, dcol, datacol;

  Do() {
    vertical_region(k_start, k_start) {
      tridiagonal_forward(acol, bcol, ccol, dcol);
    }
    
    vertical_region(k_start + 1, k_end - 1) {
      tridiagonal_forward(acol, bcol, ccol, dcol);
    }
    
    vertical_region(k_end , k_end) {
      tridiagonal_forward(acol, bcol, ccol, dcol);
    }
    
    vertical_region(k_end, k_end) {
      tridiagonal_backward(ccol, dcol, datacol);
    }
    
    vertical_region(k_end - 1, k_start) {
      tridiagonal_backward(ccol, dcol, datacol);
    }
  }
};

