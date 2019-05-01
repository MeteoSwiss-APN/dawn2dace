//===--------------------------------------------------------------------------------*- C++ -*-===//
//
//                      _       _                         _
//                     | |     | |                       | |
//                 __ _| |_ ___| | __ _ _ __   __ _    __| |_   _  ___ ___  _ __ ___
//                / _` | __/ __| |/ _` | '_ \ / _` |  / _` | | | |/ __/ _ \| '__/ _ \
//               | (_| | || (__| | (_| | | | | (_| | | (_| | |_| | (_| (_) | | |  __/
//                \__, |\__\___|_|\__,_|_| |_|\__, |  \__,_|\__, |\___\___/|_|  \___|
//                 __/ |                       __/ |         __/ |
//                |___/                       |___/         |___/
//
//                       - applied exaples of the gtclang/dawn toolchain to the COSMO dynamical core
//
//  This file is distributed under the MIT License (MIT).
//  See LICENSE.txt for details.
//===------------------------------------------------------------------------------------------===//
#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

stencil coriolis_stencil {
  /* output fields */
  storage u_tens, v_tens;
  /* input fields */
  storage u_nnow, v_nnow;
  storage fc;

  Do() {
    vertical_region(k_start, k_end) {
      u_tens += 0.25 * (fc * (v_nnow + v_nnow[i + 1]) +
                        fc[j - 1] * (v_nnow[j - 1] + v_nnow[i + 1, j - 1]));
      v_tens -= 0.25 * (fc * (u_nnow + u_nnow[j + 1]) +
                        fc[i - 1] * (u_nnow[i - 1] + u_nnow[i - 1, j + 1]));
    }
  }
};
