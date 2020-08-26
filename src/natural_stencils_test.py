from test_helpers import *

def lap2D(data, i, j, k, plus=None, minus=None):
    if plus is None and minus is None:
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

def type2(data, crlato, crlatu, hdmask, I, J, K, halo):
    lap = Zeros(I, J, K)
    for i in range(1, I-1):
        for j in range(1, J-1):
            for k in range(0, K):
                lap[i,j,k] = lap2D(data, i, j, k, crlato, crlatu)

    out = Zeros(I, J, K)
    for i in range(halo, I-halo):
        for j in range(halo, J-halo):
            for k in range(0, K):
                delta_flux_x = diffusive_flux_x(lap, data, i, j, k) - diffusive_flux_x(lap, data, i-1, j, k)
                delta_flux_y = diffusive_flux_y(lap, data, crlato, i, j, k) - diffusive_flux_y(lap, data, crlato, i, j-1, k)
                out[i,j,k] = data[i,j,k] - hdmask[i,j,k] * (delta_flux_x + delta_flux_y)
    return out

def smag(u, v, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0, I, J, K, halo):
    eddlon = 5729.58
    eddlat = 5729.58
    T_sqr_s = Zeros(I, J, K)
    for i in range(1, I):
        for j in range(1, J):
            for k in range(0, K):
                frac_1_dx = acrlat0[j] * eddlon
                frac_1_dy = eddlat / 6371.229e3

                T_s = (v[i,j-1,k] - v[i,j,k]) * frac_1_dy - (u[i-1,j,k] - u[i,j,k]) * frac_1_dx
                T_sqr_s[i,j,k] = T_s * T_s

    S_sqr_uv = Zeros(I, J, K)
    for i in range(0, I-1):
        for j in range(0, J-1):
            for k in range(0, K):
                frac_1_dx = acrlat0[j] * eddlon
                frac_1_dy = eddlat / 6371.229e3

                S_uv = (u[i,j+1,k] - u[i,j,k]) * frac_1_dy - (v[i+1,j,k] - v[i,j,k]) * frac_1_dx
                S_sqr_uv[i,j,k] = S_uv * S_uv

    u_out = Zeros(I, J, K)
    v_out = Zeros(I, J, K)
    for i in range(halo, I-halo):
        for j in range(halo, J-halo):
            for k in range(0, K):
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
        I,J,K = 4,4,4
        halo = 1
        u = Iota(I,J,K)
        v = Iota(I,J,K)
        fc = Iota(I,J)
        u_tens = Zeros(I,J,K)
        v_tens = Zeros(I,J,K)
        u_tens_dace = numpy.copy(u_tens)
        v_tens_dace = numpy.copy(v_tens)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    # u_tens += 0.25 * (fc * (v + v[i+1]) + fc[j-1] * (v[j-1] + v[i+1,j-1]));
                    u_tens[i,j,k] += 0.25 * (fc[i,j] * (v[i,j,k] + v[i+1,j,k]) + fc[i,j-1] * (v[i,j-1,k] + v[i+1,j-1,k]))
                    # v_tens -= 0.25 * (fc * (u + u[j+1]) + fc[i-1] * (u[i-1] + u[i-1,j+1]));
                    v_tens[i,j,k] -= 0.25 * (fc[i,j] * (u[i,j,k] + u[i,j+1,k]) + fc[i-1,j] * (u[i-1,j,k] + u[i-1,j+1,k]))

        u = Transpose(u)
        v = Transpose(v)
        fc = Transpose(fc)
        u_tens = Transpose(u_tens)
        v_tens = Transpose(v_tens)
        u_tens_dace = Transpose(u_tens_dace)
        v_tens_dace = Transpose(v_tens_dace)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations()
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            u_tens = u_tens_dace,
            v_tens = v_tens_dace,
            u = u,
            v = v,
            fc = fc,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(u_tens, u_tens_dace)
        self.assertEqual(v_tens, v_tens_dace)
        

class thomas(LegalSDFG, Asserts):
    def test_4_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        a = Iota(I,J,K,0)
        b = Iota(I,J,K,9)
        c = Iota(I,J,K,1)
        d = Iota(I,J,K,6)
        data = Zeros(I, J, K)
        a_dace = numpy.copy(a)
        b_dace = numpy.copy(b)
        c_dace = numpy.copy(c)
        d_dace = numpy.copy(d)
        data_dace = numpy.copy(data)

        # Do(k_from = k_start, k_to = k_start) {
        #     const double divided = 1.0 / b;
        #     c = c * divided;
        #     d = d * divided;
        # }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, 1):
                    divided = 1.0 / b[i,j,k]
                    c[i,j,k] = c[i,j,k] * divided
                    d[i,j,k] = d[i,j,k] * divided

        # Do(k_from = k_start + 1, k_to = k_end - 1) {
        #     const double divided = 1.0 / (b - (c[k - 1] * a));
        #     c = c * divided;
        #     d = d - (d[k - 1] * a) * divided;
        # }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(1, K-1):
                    divided = 1.0 / (b[i,j,k] - (c[i,j,k-1] * a[i,j,k]))
                    c[i,j,k] = c[i,j,k] * divided
                    d[i,j,k] = d[i,j,k] - (d[i,j,k-1] * a[i,j,k]) * divided

        # Do(k_from = k_end, k_to = k_end) {
        #     const double divided = 1.0 / (b - (c[k - 1] * a));
        #     d = (d - (d[k - 1] * a)) * divided;
        # }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(K-1, K):
                    divided = 1.0 / (b[i,j,k] - (c[i,j,k-1] * a[i,j,k]))
                    d[i,j,k] = (d[i,j,k] - (d[i,j,k-1] * a[i,j,k])) * divided

        # Do(k_from = k_end, k_to = k_end) { data = d; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(K-1, K):
                    data[i,j,k] = d[i,j,k]

        # Do(k_from = k_start, k_to = k_end - 1) { data = d - (c * data[k + 1]); }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in reversed(range(0, K-1)):
                    data[i,j,k] = d[i,j,k] - (c[i,j,k] * data[i,j,k+1])

        a = Transpose(a)
        b = Transpose(b)
        c = Transpose(c)
        d = Transpose(d)
        data = Transpose(data)
        a_dace = Transpose(a_dace)
        b_dace = Transpose(b_dace)
        c_dace = Transpose(c_dace)
        d_dace = Transpose(d_dace)
        data_dace = Transpose(data_dace)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations()
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            acol = a_dace,
            bcol = b_dace,
            ccol = c_dace,
            dcol = d_dace,
            datacol = data_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertIsClose(a, a_dace)
        self.assertIsClose(b, b_dace)
        self.assertIsClose(c, c_dace)
        self.assertIsClose(d, d_dace)
        self.assertIsClose(data, data_dace)

class diffusion(LegalSDFG, Asserts):
    def test_4_numerically(self):
        I,J,K = 6,6,6
        halo = 2
        input = numpy.sqrt(Iota(I, J, K))
        output = Zeros(I, J, K)
        output_dace = numpy.copy(output)

        lap = Zeros(I, J, K)
        for i in range(1, I-1):
            for j in range(1, J-1):
                for k in range(0, K):
                    lap[i,j,k] = lap2D(input, i, j, k)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = diffusive_flux_x(lap, input, i, j, k) - diffusive_flux_x(lap, input, i-1, j, k)

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations()
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertIsClose(output, output_dace)

class laplace(LegalSDFG, Asserts):
    def test_4_numerically(self):
        I,J,K = 4,4,4
        halo = 1
        input = numpy.sqrt(Iota(I, J, K))
        output = Zeros(I, J, K)
        output_dace = numpy.copy(output)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = lap2D(input, i, j, k)

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        from dace.transformation.dataflow import MapFission, MapCollapse, MapFusion
        from dace.transformation.interstate import InlineSDFG, StateFusion

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations()
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertIsClose(output, output_dace)

class laplap(LegalSDFG, Asserts):
    def test_4_numerically(self):
        I,J,K = 6,6,6
        halo = 2
        input = numpy.sqrt(Iota(I, J, K))
        output = Zeros(I, J, K)
        lap = Zeros(I, J, K)
        output_dace = numpy.copy(output)

        for i in range(halo-1, I-halo+1):
            for j in range(halo-1, J-halo+1):
                for k in range(0, K):
                    lap[i,j,k] = lap2D(input, i, j, k)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = lap2D(lap, i, j, k)

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        from dace.transformation.dataflow import MapFission, MapCollapse, MapFusion
        from dace.transformation.interstate import InlineSDFG, StateFusion

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations()
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded_st.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertIsClose(output, output_dace)

class smagorinsky(LegalSDFG, Asserts):
    def test_4_numerically(self):
        I,J,K = 16,16,5
        halo = 3
        u_in = Waves(8.0, 2.0, 1.5, 1.5, 2.0, 4.0, I, J, K)
        v_in = Waves(6.0, 1.0, 0.9, 1.1, 2.0, 4.0, I, J, K)
        hdmask = Waves(1.3, 0.20, 1.15, 1.25, 0.30, 0.41, I, J, K)
        crlavo = Waves(6.5, 1.2, 1.7, 1.9, 2.1, 2.0, J=J)
        crlavu = Waves(5.0, 2.2, 1.7, 1.9, 2.0, 1.0, J=J)
        crlato = Waves(6.5, 1.2, 1.7, 0.9, 2.1, 2.0, J=J)
        crlatu = Waves(5.0, 2.2, 1.7, 0.9, 2.0, 1.0, J=J)
        acrlat0 = Waves(6.5, 1.2, 1.2, 1.2, 2.2, 2.2, J=J)

        u_out = Zeros(I, J, K)
        v_out = Zeros(I, J, K)
        u_out_dace = numpy.copy(u_out)
        v_out_dace = numpy.copy(v_out)

        u_out, v_out = smag(u_in, v_in, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0, I, J, K, halo)

        u_in = Transpose(u_in)
        v_in = Transpose(v_in)
        hdmask = Transpose(hdmask)
        acrlat0 = Transpose(acrlat0)
        crlavo = Transpose(crlavo)
        crlavu = Transpose(crlavu)
        crlato = Transpose(crlato)
        crlatu = Transpose(crlatu)
        u_out = Transpose(u_out)
        v_out = Transpose(v_out)
        u_out_dace = Transpose(u_out_dace)
        v_out_dace = Transpose(v_out_dace)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations()
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
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        print("u_in")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, u_in[j,k,i])
        print("v_in")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, v_in[j,k,i])

        print("u_out")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, u_out[j,k,i], u_out_dace[j,k,i], u_out[j,k,i] - u_out_dace[j,k,i])
        print("v_out")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, v_out[j,k,i], v_out_dace[j,k,i], v_out[j,k,i] - v_out_dace[j,k,i])

        self.assertIsClose(u_out, u_out_dace)
        self.assertIsClose(v_out, v_out_dace)


class horizontal_diffusion(LegalSDFG, Asserts):
    def test_4_numerically(self):
        I,J,K = 16,16,5
        halo = 4
        u_in = Waves(1.80, 1.20, 0.15, 1.15, 0.20, 1.40, I, J, K)
        v_in = Waves(1.60, 1.10, 0.09, 1.11, 0.20, 1.40, I, J, K)
        w_in = Waves(1.60, 1.10, 0.09, 1.11, 0.20, 1.40, I, J, K)
        pp_in = Waves(1.30, 1.20, 0.27, 1.12, 0.10, 1.50, I, J, K)
        hdmask = Waves(0.3, 1.22, 0.17, 1.19, 0.20, 1.40, I, J, K)
        crlavo = Waves(1.65, 1.12, 0.17, 1.19, 0.21, 1.20, J=J)
        crlavu = Waves(1.50, 1.22, 0.17, 1.19, 0.20, 1.10, J=J)
        crlato = Waves(1.65, 1.12, 0.17, 1.09, 0.21, 1.20, J=J)
        crlatu = Waves(1.50, 1.22, 0.17, 1.09, 0.20, 1.10, J=J)
        acrlat0 = Waves(1.65, 1.22, 0.11, 1.52, 0.42, 1.02, J=J)
        u_out = Zeros(I,J,K)
        v_out = Zeros(I,J,K)
        w_out = Zeros(I,J,K)
        pp_out = Zeros(I,J,K)
        u_out_dace = numpy.copy(u_out)
        v_out_dace = numpy.copy(v_out)
        w_out_dace = numpy.copy(w_out)
        pp_out_dace = numpy.copy(pp_out)

        u_tmp = type2(u_in, crlato, crlatu, hdmask, I, J, K, 2)
        v_tmp = type2(v_in, crlato, crlatu, hdmask, I, J, K, 2)
        w_out = type2(w_in, crlato, crlatu, hdmask, I, J, K, halo)
        pp_out = type2(pp_in, crlato, crlatu, hdmask, I, J, K, halo)
        u_out, v_out = smag(u_tmp, v_tmp, hdmask, crlavo, crlavu, crlato, crlatu, acrlat0, I, J, K, halo)

        u_in = Transpose(u_in)
        v_in = Transpose(v_in)
        w_in = Transpose(w_in)
        pp_in = Transpose(pp_in)
        hdmask = Transpose(hdmask)
        acrlat0 = Transpose(acrlat0)
        crlavo = Transpose(crlavo)
        crlavu = Transpose(crlavu)
        crlato = Transpose(crlato)
        crlatu = Transpose(crlatu)
        u_out = Transpose(u_out)
        v_out = Transpose(v_out)
        w_out = Transpose(w_out)
        pp_out = Transpose(pp_out)
        u_out_dace = Transpose(u_out_dace)
        v_out_dace = Transpose(v_out_dace)
        w_out_dace = Transpose(w_out_dace)
        pp_out_dace = Transpose(pp_out_dace)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations()
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
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        print("u_in")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, u_in[j,k,i])
        print("v_in")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, v_in[j,k,i])
        print("w_in")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, w_in[j,k,i])
        print("pp_in")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, pp_in[j,k,i])


        print("u_out")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, u_out[j,k,i], u_out_dace[j,k,i], u_out[j,k,i] - u_out_dace[j,k,i])
        print("v_out")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, v_out[j,k,i], v_out_dace[j,k,i], v_out[j,k,i] - v_out_dace[j,k,i])
        print("w_out")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, w_out[j,k,i], w_out_dace[j,k,i], w_out[j,k,i] - w_out_dace[j,k,i])
        print("pp_out")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, pp_out[j,k,i], pp_out_dace[j,k,i], pp_out[j,k,i] - pp_out_dace[j,k,i])

        self.assertIsClose(w_out, w_out_dace)
        self.assertIsClose(pp_out, pp_out_dace)
        self.assertIsClose(u_out, u_out_dace)
        self.assertIsClose(v_out, v_out_dace)
        
class type2_diffusion(LegalSDFG, Asserts):
    def test_4_numerically(self):
        I,J,K = 16,16,5
        halo = 3
        u_in = Waves(1.80, 1.20, 0.15, 1.15, 0.20, 1.40, I, J, K)
        v_in = Waves(1.60, 1.10, 0.09, 1.11, 0.20, 1.40, I, J, K)
        w_in = Waves(1.60, 1.10, 0.09, 1.11, 0.20, 1.40, I, J, K)
        pp_in = Waves(1.30, 1.20, 0.27, 1.12, 0.10, 1.50, I, J, K)
        hdmask = Waves(0.3, 1.22, 0.17, 1.19, 0.20, 1.40, I, J, K)
        crlavo = Waves(1.65, 1.12, 0.17, 1.19, 0.21, 1.20, J=J)
        crlavu = Waves(1.50, 1.22, 0.17, 1.19, 0.20, 1.10, J=J)
        crlato = Waves(1.65, 1.12, 0.17, 1.09, 0.21, 1.20, J=J)
        crlatu = Waves(1.50, 1.22, 0.17, 1.09, 0.20, 1.10, J=J)
        acrlat0 = Waves(1.65, 1.22, 0.11, 1.52, 0.42, 1.02, J=J)
        u_out = Zeros(I,J,K)
        v_out = Zeros(I,J,K)
        w_out = Zeros(I,J,K)
        pp_out = Zeros(I,J,K)
        u_out_dace = numpy.copy(u_out)
        v_out_dace = numpy.copy(v_out)
        w_out_dace = numpy.copy(w_out)
        pp_out_dace = numpy.copy(pp_out)

        u_out = type2(u_in, crlato, crlatu, hdmask, I, J, K, halo)
        v_out = type2(v_in, crlato, crlatu, hdmask, I, J, K, halo)
        w_out = type2(w_in, crlato, crlatu, hdmask, I, J, K, halo)
        pp_out = type2(pp_in, crlato, crlatu, hdmask, I, J, K, halo)

        u_in = Transpose(u_in)
        v_in = Transpose(v_in)
        w_in = Transpose(w_in)
        pp_in = Transpose(pp_in)
        hdmask = Transpose(hdmask)
        acrlat0 = Transpose(acrlat0)
        crlavo = Transpose(crlavo)
        crlavu = Transpose(crlavu)
        crlato = Transpose(crlato)
        crlatu = Transpose(crlatu)
        u_out = Transpose(u_out)
        v_out = Transpose(v_out)
        w_out = Transpose(w_out)
        pp_out = Transpose(pp_out)
        u_out_dace = Transpose(u_out_dace)
        v_out_dace = Transpose(v_out_dace)
        w_out_dace = Transpose(w_out_dace)
        pp_out_dace = Transpose(pp_out_dace)

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg.apply_strict_transformations()
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
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        print("u_in")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, u_in[j,k,i])
        print("v_in")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, v_in[j,k,i])
        print("w_in")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, w_in[j,k,i])
        print("pp_in")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, pp_in[j,k,i])


        print("u_out")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, u_out[j,k,i], u_out_dace[j,k,i], u_out[j,k,i] - u_out_dace[j,k,i])
        print("v_out")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, v_out[j,k,i], v_out_dace[j,k,i], v_out[j,k,i] - v_out_dace[j,k,i])
        print("w_out")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, w_out[j,k,i], w_out_dace[j,k,i], w_out[j,k,i] - w_out_dace[j,k,i])
        print("pp_out")
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    print(i,j,k, pp_out[j,k,i], pp_out_dace[j,k,i], pp_out[j,k,i] - pp_out_dace[j,k,i])

        self.assertIsClose(w_out, w_out_dace)
        self.assertIsClose(pp_out, pp_out_dace)
        self.assertIsClose(u_out, u_out_dace)
        self.assertIsClose(v_out, v_out_dace)
        

if __name__ == '__main__':
    unittest.main()
    