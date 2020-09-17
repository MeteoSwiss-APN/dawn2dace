from test_helpers import *

def lap2D(data, i, j, k, plus=None, minus=None):
    if (plus is None) and (minus is None):
        return data[i-1,j,k] + data[i+1,j,k] - 2.0 * data[i,j,k] \
            + (data[i,j+1,k] - data[i,j,k]) \
            + (data[i,j-1,k] - data[i,j,k])

    return data[i-1,j,k] + data[i+1,j,k] - 2.0 * data[i,j,k] \
        + plus[j] * (data[i,j+1,k] - data[i,j,k]) \
        + minus[j] * (data[i,j-1,k] - data[i,j,k])


def diffusive_flux_x(lap, data, i, j, k):
    flx = lap[i+1,j,k] - lap[i,j,k]
    return 0.0 if (flx * (data[i+1,j,k] - data[i,j,k])) > 0.0 else flx

def diffusive_flux_y(lap, data, crlato, i, j, k):
    fly = crlato[j] * (lap[i,j+1,k] - lap[i,j,k])
    return 0.0 if (fly * (data[i,j+1,k] - data[i,j,k])) > 0.0 else fly

def type2(data, crlato, crlatu, hdmask, dim, halo=None):
    halo = halo or dim.halo
    lap = Zeros(dim.ijk)
    for i in range(1, dim.I-1):
        for j in range(1, dim.J-1):
            for k in range(0, dim.K):
                lap[i,j,k] = lap2D(data, i, j, k, crlato, crlatu)

    out = Zeros(dim.ijk)
    for i in range(halo, dim.I-halo):
        for j in range(halo, dim.J-halo):
            for k in range(0, dim.K):
                delta_flux_x = diffusive_flux_x(lap, data, i, j, k) - diffusive_flux_x(lap, data, i-1, j, k)
                delta_flux_y = diffusive_flux_y(lap, data, crlato, i, j, k) - diffusive_flux_y(lap, data, crlato, i, j-1, k)
                out[i,j,k] = data[i,j,k] - hdmask[i,j,k] * (delta_flux_x + delta_flux_y)
    return out

def smag(u, v, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0, dim):
    eddlon = 5729.58
    eddlat = 5729.58
    T_sqr_s = Zeros(dim.ijk)
    for i in range(1, dim.I):
        for j in range(1, dim.J):
            for k in range(0, dim.K):
                frac_1_dx = acrlat0[j] * eddlon
                frac_1_dy = eddlat / 6371.229e3

                T_s = (v[i,j-1,k] - v[i,j,k]) * frac_1_dy - (u[i-1,j,k] - u[i,j,k]) * frac_1_dx
                T_sqr_s[i,j,k] = T_s * T_s

    S_sqr_uv = Zeros(dim.ijk)
    for i in range(0, dim.I-1):
        for j in range(0, dim.J-1):
            for k in range(0, dim.K):
                frac_1_dx = acrlat0[j] * eddlon
                frac_1_dy = eddlat / 6371.229e3

                S_uv = (u[i,j+1,k] - u[i,j,k]) * frac_1_dy - (v[i+1,j,k] - v[i,j,k]) * frac_1_dx
                S_sqr_uv[i,j,k] = S_uv * S_uv

    u_out = Zeros(dim.ijk)
    v_out = Zeros(dim.ijk)
    for i in range(dim.halo, dim.I-dim.halo):
        for j in range(dim.halo, dim.J-dim.halo):
            for k in range(0, dim.K):
                weight_smag = 0.5
                tau_smag = 0.3
                hdweight = weight_smag * hdmask[i,j,k]

                smag_u = tau_smag * numpy.sqrt(0.5 * (T_sqr_s[i,j,k] + T_sqr_s[i+1,j,k]) + 0.5 * (S_sqr_uv[i,j,k] + S_sqr_uv[i,j-1,k])) - hdweight
                smag_u = min(0.5, max(0.0, smag_u))
                u_out[i,j,k] = u[i,j,k] + smag_u * lap2D(u, i, j, k, crlato, crlatu)

                smag_v = tau_smag * numpy.sqrt(0.5 * (T_sqr_s[i,j,k] + T_sqr_s[i,j+1,k]) + 0.5 * (S_sqr_uv[i,j,k] + S_sqr_uv[i-1,j,k])) - hdweight
                smag_v = min(0.5, max(0.0, smag_v))
                v_out[i,j,k] = v[i,j,k] + smag_v * lap2D(v, i, j, k, crlavo, crlavu)
    return u_out, v_out

class coriolis(LegalSDFG, Asserts):
    def test_4_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], halo=1)
        u = Waves(8.0, 2.0, 1.5, 1.5, 2.0, 4.0, dim.ijk);
        v = Waves(5.0, 1.2, 1.3, 1.7, 2.2, 3.5, dim.ijk);
        fc = Waves(2.0, 1.2, 1.3, 1.7, 2.2, 3.5, dim.ij);
        u_tens = Zeros(dim.ijk)
        v_tens = Zeros(dim.ijk)
        u_tens_dace = Zeros(dim.ijk)
        v_tens_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    # u_tens += 0.25 * (fc * (v + v[i+1]) + fc[j-1] * (v[j-1] + v[i+1,j-1]));
                    u_tens[i,j,k] += 0.25 * (fc[i,j] * (v[i,j,k] + v[i+1,j,k]) + fc[i,j-1] * (v[i,j-1,k] + v[i+1,j-1,k]))
                    # v_tens -= 0.25 * (fc * (u + u[j+1]) + fc[i-1] * (u[i-1] + u[i-1,j+1]));
                    v_tens[i,j,k] -= 0.25 * (fc[i,j] * (u[i,j,k] + u[i,j+1,k]) + fc[i-1,j] * (u[i-1,j,k] + u[i-1,j+1,k]))

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            u_tens = u_tens_dace,
            v_tens = v_tens_dace,
            u = u,
            v = v,
            fc = fc,
            **dim.ProgramArguments())

        self.assertEqual(u_tens, u_tens_dace)
        self.assertEqual(v_tens, v_tens_dace)
        

class thomas(LegalSDFG, Asserts):
    def test_4_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], halo=0)
        a = Iota(dim.ijk,0)
        b = Iota(dim.ijk,9)
        c = Iota(dim.ijk,1)
        d = Iota(dim.ijk,6)
        data = Zeros(dim.ijk)
        a_dace = Iota(dim.ijk,0)
        b_dace = Iota(dim.ijk,9)
        c_dace = Iota(dim.ijk,1)
        d_dace = Iota(dim.ijk,6)
        data_dace = Zeros(dim.ijk)

        # Do(k_from = k_start, k_to = k_start) {
        #     const double divided = 1.0 / b;
        #     c = c * divided;
        #     d = d * divided;
        # }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, 1):
                    divided = 1.0 / b[i,j,k]
                    c[i,j,k] = c[i,j,k] * divided
                    d[i,j,k] = d[i,j,k] * divided

        # Do(k_from = k_start + 1, k_to = k_end - 1) {
        #     const double divided = 1.0 / (b - (c[k - 1] * a));
        #     c = c * divided;
        #     d = d - (d[k - 1] * a) * divided;
        # }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(1, dim.K-1):
                    divided = 1.0 / (b[i,j,k] - (c[i,j,k-1] * a[i,j,k]))
                    c[i,j,k] = c[i,j,k] * divided
                    d[i,j,k] = d[i,j,k] - (d[i,j,k-1] * a[i,j,k]) * divided

        # Do(k_from = k_end, k_to = k_end) {
        #     const double divided = 1.0 / (b - (c[k - 1] * a));
        #     d = (d - (d[k - 1] * a)) * divided;
        # }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(dim.K-1, dim.K):
                    divided = 1.0 / (b[i,j,k] - (c[i,j,k-1] * a[i,j,k]))
                    d[i,j,k] = (d[i,j,k] - (d[i,j,k-1] * a[i,j,k])) * divided

        # Do(k_from = k_end, k_to = k_end) { data = d; }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(dim.K-1, dim.K):
                    data[i,j,k] = d[i,j,k]

        # Do(k_from = k_start, k_to = k_end - 1) { data = d - (c * data[k + 1]); }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in reversed(range(0, dim.K-1)):
                    data[i,j,k] = d[i,j,k] - (c[i,j,k] * data[i,j,k+1])

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            acol = a_dace,
            bcol = b_dace,
            ccol = c_dace,
            dcol = d_dace,
            datacol = data_dace,
            **dim.ProgramArguments())

        self.assertIsClose(a, a_dace)
        self.assertIsClose(b, b_dace)
        self.assertIsClose(c, c_dace)
        self.assertIsClose(d, d_dace)
        self.assertIsClose(data, data_dace)

class diffusion(LegalSDFG, Asserts):
    def test_4_numerically(self):
        dim = Dimensions([6,6,6], [6,6,7], halo=2)
        input = numpy.sqrt(Iota(dim.ijk))
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        lap = Zeros(dim.ijk)
        for i in range(1, dim.I-1):
            for j in range(1, dim.J-1):
                for k in range(0, dim.K):
                    lap[i,j,k] = lap2D(input, i, j, k)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = diffusive_flux_x(lap, input, i, j, k) - diffusive_flux_x(lap, input, i-1, j, k)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertIsClose(output, output_dace)

class laplace(LegalSDFG, Asserts):
    def test_4_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], halo=1)
        input = numpy.sqrt(Iota(dim.ijk))
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = lap2D(input, i, j, k)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertIsClose(output, output_dace)

class laplap(LegalSDFG, Asserts):
    def test_4_numerically(self):
        dim = Dimensions([6,6,6], [6,6,7], halo=2)
        input = numpy.sqrt(Iota(dim.ijk))
        output = Zeros(dim.ijk)
        lap = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        for i in range(dim.halo-1, dim.I-dim.halo+1):
            for j in range(dim.halo-1, dim.J-dim.halo+1):
                for k in range(0, dim.K):
                    lap[i,j,k] = lap2D(input, i, j, k)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = lap2D(lap, i, j, k)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertIsClose(output, output_dace)

class smagorinsky(LegalSDFG, Asserts):
    def test_4_numerically(self):
        dim = Dimensions([16,16,5], [16,16,6], halo=3)

        u_in = Waves(8.0, 2.0, 1.5, 1.5, 2.0, 4.0, dim.ijk)
        v_in = Waves(6.0, 1.0, 0.9, 1.1, 2.0, 4.0, dim.ijk)
        hdmask = Waves(1.3, 0.20, 1.15, 1.25, 0.30, 0.41, dim.ijk)
        crlavo = Waves(6.5, 1.2, 1.7, 1.9, 2.1, 2.0, dim.j)
        crlavu = Waves(5.0, 2.2, 1.7, 1.9, 2.0, 1.0, dim.j)
        crlato = Waves(6.5, 1.2, 1.7, 0.9, 2.1, 2.0, dim.j)
        crlatu = Waves(5.0, 2.2, 1.7, 0.9, 2.0, 1.0, dim.j)
        acrlat0 = Waves(6.5, 1.2, 1.2, 1.2, 2.2, 2.2, dim.j)

        u_out = Zeros(dim.ijk)
        v_out = Zeros(dim.ijk)

        u_out_dace = Zeros(dim.ijk)
        v_out_dace = Zeros(dim.ijk)

        u_out, v_out = smag(u_in, v_in, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0, dim)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            u_in = u_in,
            v_in = v_in,
            hdmask = hdmask,
            acrlat0 = acrlat0,
            crlavo = crlavo,
            crlavu = crlavu,
            crlato = crlato,
            crlatu = crlatu,
            u_out = u_out_dace,
            v_out = v_out_dace,
            **dim.ProgramArguments())

        # print("u_in")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, u_in[i,j,k])
        # print("v_in")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, v_in[i,j,k])

        # print("u_out")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, u_out[i,j,k], u_out_dace[i,j,k], u_out[i,j,k] - u_out_dace[i,j,k])
        # print("v_out")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, v_out[i,j,k], v_out_dace[i,j,k], v_out[i,j,k] - v_out_dace[i,j,k])

        self.assertIsClose(u_out, u_out_dace)
        self.assertIsClose(v_out, v_out_dace)


class horizontal_diffusion(LegalSDFG, Asserts):
    def test_4_numerically(self):
        dim = Dimensions([16,16,5], [16,16,6], halo=4)
        u_in = Waves(1.80, 1.20, 0.15, 1.15, 0.20, 1.40, dim.ijk)
        v_in = Waves(1.60, 1.10, 0.09, 1.11, 0.20, 1.40, dim.ijk)
        w_in = Waves(1.60, 1.10, 0.09, 1.11, 0.20, 1.40, dim.ijk)
        pp_in = Waves(1.30, 1.20, 0.27, 1.12, 0.10, 1.50, dim.ijk)
        hdmask = Waves(0.3, 1.22, 0.17, 1.19, 0.20, 1.40, dim.ijk)
        crlavo = Waves(1.65, 1.12, 0.17, 1.19, 0.21, 1.20, dim.j)
        crlavu = Waves(1.50, 1.22, 0.17, 1.19, 0.20, 1.10, dim.j)
        crlato = Waves(1.65, 1.12, 0.17, 1.09, 0.21, 1.20, dim.j)
        crlatu = Waves(1.50, 1.22, 0.17, 1.09, 0.20, 1.10, dim.j)
        acrlat0 = Waves(1.65, 1.22, 0.11, 1.52, 0.42, 1.02, dim.j)
        u_out = Zeros(dim.ijk)
        v_out = Zeros(dim.ijk)
        w_out = Zeros(dim.ijk)
        pp_out = Zeros(dim.ijk)
        u_out_dace = Zeros(dim.ijk)
        v_out_dace = Zeros(dim.ijk)
        w_out_dace = Zeros(dim.ijk)
        pp_out_dace = Zeros(dim.ijk)

        u_tmp = type2(u_in, crlato, crlatu, hdmask, dim, 2)
        v_tmp = type2(v_in, crlato, crlatu, hdmask, dim, 2)
        w_out = type2(w_in, crlato, crlatu, hdmask, dim)
        pp_out = type2(pp_in, crlato, crlatu, hdmask, dim)
        u_out, v_out = smag(u_tmp, v_tmp, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0, dim)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.apply_transformations_repeated([MapExpansion])
        sdfg.apply_transformations_repeated([MapFusion])
        sdfg.apply_transformations_repeated([MapCollapse])
        sdfg.save("gen/" + self.__class__.__name__ + "_optimized.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            acrlat0 = acrlat0,
            crlavo = crlavo,
            crlavu = crlavu,
            crlato = crlato,
            crlatu = crlatu,
            hdmask = hdmask,
            pp_out = pp_out_dace,
            pp_in = pp_in,
            u_out = u_out_dace,
            u_in = u_in,
            v_out = v_out_dace,
            v_in = v_in,
            w_out = w_out_dace,
            w_in = w_in,
            **dim.ProgramArguments())

        # print("u_in")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, u_in[i,j,k])
        # print("v_in")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, v_in[i,j,k])
        # print("w_in")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, w_in[i,j,k])
        # print("pp_in")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, pp_in[i,j,k])


        # print("u_out")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, u_out[i,j,k], u_out_dace[i,j,k], u_out[i,j,k] - u_out_dace[i,j,k])
        # print("v_out")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, v_out[i,j,k], v_out_dace[i,j,k], v_out[i,j,k] - v_out_dace[i,j,k])
        # print("w_out")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, w_out[i,j,k], w_out_dace[i,j,k], w_out[i,j,k] - w_out_dace[i,j,k])
        # print("pp_out")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, pp_out[i,j,k], pp_out_dace[i,j,k], pp_out[i,j,k] - pp_out_dace[i,j,k])

        self.assertIsClose(w_out, w_out_dace)
        self.assertIsClose(pp_out, pp_out_dace)
        self.assertIsClose(u_out, u_out_dace)
        self.assertIsClose(v_out, v_out_dace)
        
class type2_diffusion(LegalSDFG, Asserts):
    def test_4_numerically(self):
        dim = Dimensions([16,16,5], [16,16,6], halo=2)
        u_in = Waves(1.80, 1.20, 0.15, 1.15, 0.20, 1.40, dim.ijk)
        v_in = Waves(1.60, 1.10, 0.09, 1.11, 0.20, 1.40, dim.ijk)
        w_in = Waves(1.60, 1.10, 0.09, 1.11, 0.20, 1.40, dim.ijk)
        pp_in = Waves(1.30, 1.20, 0.27, 1.12, 0.10, 1.50, dim.ijk)
        hdmask = Waves(0.3, 1.22, 0.17, 1.19, 0.20, 1.40, dim.ijk)
        crlavo = Waves(1.65, 1.12, 0.17, 1.19, 0.21, 1.20, dim.j)
        crlavu = Waves(1.50, 1.22, 0.17, 1.19, 0.20, 1.10, dim.j)
        crlato = Waves(1.65, 1.12, 0.17, 1.09, 0.21, 1.20, dim.j)
        crlatu = Waves(1.50, 1.22, 0.17, 1.09, 0.20, 1.10, dim.j)
        acrlat0 = Waves(1.65, 1.22, 0.11, 1.52, 0.42, 1.02, dim.j)
        u_out = Zeros(dim.ijk)
        v_out = Zeros(dim.ijk)
        w_out = Zeros(dim.ijk)
        pp_out = Zeros(dim.ijk)
        u_out_dace = Zeros(dim.ijk)
        v_out_dace = Zeros(dim.ijk)
        w_out_dace = Zeros(dim.ijk)
        pp_out_dace = Zeros(dim.ijk)

        u_out = type2(u_in, crlato, crlatu, hdmask, dim)
        v_out = type2(v_in, crlato, crlatu, hdmask, dim)
        w_out = type2(w_in, crlato, crlatu, hdmask, dim)
        pp_out = type2(pp_in, crlato, crlatu, hdmask, dim)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            acrlat0 = acrlat0,
            crlavo = crlavo,
            crlavu = crlavu,
            crlato = crlato,
            crlatu = crlatu,
            hdmask = hdmask,
            pp_out = pp_out_dace,
            pp_in = pp_in,
            u_out = u_out_dace,
            u_in = u_in,
            v_out = v_out_dace,
            v_in = v_in,
            w_out = w_out_dace,
            w_in = w_in,
            **dim.ProgramArguments())

        # print("u_in")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, u_in[i,j,k])
        # print("v_in")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, v_in[i,j,k])
        # print("w_in")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, w_in[i,j,k])
        # print("pp_in")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, pp_in[i,j,k])


        # print("u_out")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, u_out[i,j,k], u_out_dace[i,j,k], u_out[i,j,k] - u_out_dace[i,j,k])
        # print("v_out")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, v_out[i,j,k], v_out_dace[i,j,k], v_out[i,j,k] - v_out_dace[i,j,k])
        # print("w_out")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, w_out[i,j,k], w_out_dace[i,j,k], w_out[i,j,k] - w_out_dace[i,j,k])
        # print("pp_out")
        # for i in range(dim.halo, dim.I-dim.halo):
        #     for j in range(dim.halo, dim.J-dim.halo):
        #         for k in range(0, dim.K):
        #             print(i,j,k, pp_out[i,j,k], pp_out_dace[i,j,k], pp_out[i,j,k] - pp_out_dace[i,j,k])

        self.assertIsClose(w_out, w_out_dace)
        self.assertIsClose(pp_out, pp_out_dace)
        self.assertIsClose(u_out, u_out_dace)
        self.assertIsClose(v_out, v_out_dace)
        

if __name__ == '__main__':
    unittest.main()
    