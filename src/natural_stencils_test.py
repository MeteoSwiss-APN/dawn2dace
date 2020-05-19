from test_helpers import *

class coriolis(LegalSDFG, Asserts):
    file_name = "coriolis"

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

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
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

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations()
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

class diffusion(LegalSDFG, Asserts):
    file_name = "diffusion"

    def test_4_numerically(self):
        I,J,K = 4,4,4
        halo = 1
        input = numpy.sqrt(Iota(I, J, K))
        output = Zeros(I, J, K)
        output_dace = numpy.copy(output)

        def laplacian(data, i, j, k):
            return data[i-1,j,k] + data[i+1,j,k] + data[i,j-1,k] + data[i,j+1,k] - 4.0 * data[i,j,k]

        def diffusive_flux_x(lap, data, i, j, k):
            flx = lap[i+1,j,k] - lap[i,j,k]
            return 0.0 if (flx * (data[i+1,j,k] - data[i,j,k])) > 0.0 else flx

        lap = Zeros(I, J, K)
        for i in range(1, I-1):
            for j in range(1, J-1):
                for k in range(0, K):
                    lap[i,j,k] = laplacian(input, i, j, k)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = diffusive_flux_x(lap, input, i, j, k) - diffusive_flux_x(lap, input, i-1, j, k)

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)

        sdfg = get_sdfg(self.file_name + ".0.iir")
        dace.graph.labeling.propagate_labels_sdfg(sdfg)
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertIsClose(output, output_dace)

class laplace(LegalSDFG, Asserts):
    file_name = "laplace"

    def test_4_numerically(self):
        I,J,K = 4,4,4
        halo = 1
        input = numpy.sqrt(Iota(I, J, K))
        output = Zeros(I, J, K)
        output_dace = numpy.copy(output)

        def laplacian(data, i, j, k):
            return data[i-1,j,k] + data[i+1,j,k] + data[i,j-1,k] + data[i,j+1,k] - 4.0 * data[i,j,k]

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = laplacian(input, i, j, k)

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        from dace.transformation.dataflow import MapFission, MapCollapse, MapFusion
        from dace.transformation.interstate import InlineSDFG, StateFusion

        sdfg = get_sdfg(self.file_name + ".0.iir")
        dace.graph.labeling.propagate_labels_sdfg(sdfg)
        sdfg.save("gen/" + self.__class__.__name__ + "_libnode.sdfg")
        sdfg.expand_library_nodes()
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        # sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertIsClose(output, output_dace)

if __name__ == '__main__':
    unittest.main()
    