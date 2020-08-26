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
//                      - applied examples of the gtclang/dawn toolchain to the COSMO dynamical core
//
//  This file is distributed under the MIT License (MIT).
//  See LICENSE.txt for details.
//===------------------------------------------------------------------------------------------===//
#include "gtclang_dsl_defs/math.hpp"
#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

globals {
  double eddlon = 2;
  double eddlat = 3;
  double tau_smag = 4;
  double weight_smag = 3.3;
};

stencil_function avg {
  offset off;
  storage in;

  Do { return 0.5 * (in[off] + in); }
};

stencil_function delta {
  offset off;
  storage data;

  Do { return data[off] - data; }
};

stencil_function laplacian {
  storage data, crlato, crlatv;

  Do {
    return data[i + 1] + data[i - 1] - 2.0 * data + crlato * delta(j + 1, data) +
           crlatv * delta(j - 1, data);
  }
};

stencil_function diffusive_flux_x {
  storage lap, data;

  Do {
    const double flx = delta(i + 1, lap);
    return (flx * delta(i + 1, data)) > 0.0 ? 0.0 : flx;
  }
};

stencil_function diffusive_flux_y {
  storage lap, data, crlato;

  Do {
    const double fly = crlato * delta(j + 1, lap);
    return (fly * delta(j + 1, data)) > 0.0 ? 0.0 : fly;
  }
};

/// Type2 - Diffusion
#pragma gtclang no_codegen
stencil type2 {
  storage out, in, crlato, crlatu, hdmask;
  var lap;

  Do {
    vertical_region(k_start, k_end) {
      lap = laplacian(in, crlato, crlatu);
      const double delta_flux_x =
          diffusive_flux_x(lap, in) - diffusive_flux_x(lap[i - 1], in[i - 1]);
      const double delta_flux_y = diffusive_flux_y(lap, in, crlato) -
                                  diffusive_flux_y(lap[j - 1], in[j - 1], crlato[j - 1]);
      out = in - hdmask * (delta_flux_x + delta_flux_y);
    }
  }
};

/// Smagorinsky - Diffusion
#pragma gtclang no_codegen
stencil smagorinsky {
  /* output fields */
  storage u_out, v_out;

  /* input fields */
  storage u_in, v_in, hdmaskvel;
  storage_j crlavo, crlavu, crlato, crlatu, acrlat0;

  /* temporary fields */
  var T_sqr_s, S_sqr_uv;

  Do {
    vertical_region(k_start, k_end) {
      const double frac_1_dx = acrlat0 * eddlon;
      const double frac_1_dy = eddlat / (double)6371.229e3;

      // Tension
      const double T_s = delta(j - 1, v_in) * frac_1_dy - delta(i - 1, u_in) * frac_1_dx;
      T_sqr_s = T_s * T_s;

      const double S_uv = delta(j + 1, u_in) * frac_1_dy + delta(i + 1, v_in) * frac_1_dx;
      S_sqr_uv = S_uv * S_uv;

      const double hdweight = weight_smag * hdmaskvel;

      // I direction
      double smag_u =
          tau_smag * math::sqrt((avg(i + 1, T_sqr_s) + avg(j - 1, S_sqr_uv))) - hdweight;
      smag_u = math::min(0.5, math::max(0.0, smag_u));

      // J direction
      double smag_v =
          tau_smag *
              math::sqrt((0.5 * (T_sqr_s + T_sqr_s[j + 1]) + 0.5 * (S_sqr_uv + S_sqr_uv[i - 1]))) -
          hdweight;
      smag_v = math::min(0.5, math::max(0.0, smag_v));

      const double lapu = u_in[i + 1] + u_in[i - 1] - 2.0 * u_in + crlato * (u_in(j + 1) - u_in) +
                          crlatu * (u_in(j - 1) - u_in);
      const double lapv = v_in[i + 1] + v_in[i - 1] - 2.0 * v_in + crlavo * (v_in(j + 1) - v_in) +
                          crlavu * (v_in(j - 1) - v_in);

      u_out = u_in + smag_u * lapu;
      v_out = v_in + smag_v * lapv;
    }
  }
};

stencil type2_diffusion {
  /* output fields */
  storage u_out, v_out, w_out, pp_out;

  /* input fields */
  storage u_in, v_in, w_in, pp_in;
  storage hdmask;
  storage_j crlavo, crlavu, crlato, crlatu, acrlat0;

  Do {
    type2(u_out, u_in, crlato, crlatu, hdmask);
    type2(v_out, v_in, crlato, crlatu, hdmask);
    type2(w_out, w_in, crlato, crlatu, hdmask);
    type2(pp_out, pp_in, crlato, crlatu, hdmask);
  }
};
