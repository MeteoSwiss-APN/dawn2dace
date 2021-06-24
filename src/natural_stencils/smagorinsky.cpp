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

/// Smagorinsky - Diffusion
stencil smagorinsky {
  /* output fields */
  storage u_out, v_out;

  /* input fields */
  storage u_in, v_in, hdmask;
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

      const double hdweight = weight_smag * hdmask;

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