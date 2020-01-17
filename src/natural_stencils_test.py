from test_helpers import *

class coriolis(LegalSDFG, Asserts):
    file_name = "coriolis"

    def test4_numerically(self):
        I,J,K = 8,8,8
        halo = 1
        u = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        v = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        fc = numpy.arange(I*J).astype(dace.float64.type).reshape(I,J)
        u_tens = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        v_tens = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        u_tens_dace = numpy.copy(u_tens)
        v_tens_dace = numpy.copy(v_tens)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                # u_tens += 0.25 * (fc * (v + v[i+1]) + fc[j-1] * (v[j-1] + v[i+1,j-1]));
                u_tens[i,j,:] += 0.25 * (fc[i,j] * (v[i,j,:] + v[i+1,j,:]) + fc[i,j-1] * (v[i,j-1,:] + v[i+1,j-1,:]))
                # v_tens -= 0.25 * (fc * (u + u[j+1]) + fc[i-1] * (u[i-1] + u[i-1,j+1]));
                v_tens[i,j,:] -= 0.25 * (fc[i,j] * (u[i,j,:] + u[i,j+1,:]) + fc[i-1,j] * (u[i-1,j,:] + u[i-1,j+1,:]))

        u = Transpose(u)
        v = Transpose(v)
        fc = TransposeIJ(fc)
        u_tens = Transpose(u_tens)
        v_tens = Transpose(v_tens)
        u_tens_dace = Transpose(u_tens_dace)
        v_tens_dace = Transpose(v_tens_dace)

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

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
    file_name = "thomas"

    def test4_numerically(self):
        I,J,K = 8,8,8
        halo = 0
        a = numpy.arange(0,0+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        b = numpy.arange(9,9+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        c = numpy.arange(1,1+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        d = numpy.arange(6,6+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        data = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
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

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

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

if __name__ == '__main__':
    unittest.main()
    