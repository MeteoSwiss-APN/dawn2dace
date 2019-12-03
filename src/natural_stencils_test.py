import unittest
import numpy
import sys
import os

# This is a workaround for a bug in vscode. Apparently it ignores PYTHONPATH. (6.Nov 2019)
sys.path.append(os.path.relpath("build/gen/iir_specification/"))
sys.path.append(os.path.relpath("../dace"))

import dawn2dace
import dace

def read_file(file_name):
    with open("gen/" + file_name, "rb") as f:
        return f.read() # IIR as binary str.
    return None

def get_sdfg(file_name):
    iir = read_file(file_name)
    return dawn2dace.IIR_str_to_SDFG(iir)

class LegalSDFG:
    def test_1_file_exists(self):
        self.assertIsNotNone(read_file(self.file_name + ".0.iir"))

    def test_2_sdfg_is_valid(self):
        sdfg = get_sdfg(self.file_name + ".0.iir")
        self.assertTrue(sdfg.is_valid())
        
    def test_3_sdfg_compiles(self):
        sdfg = get_sdfg(self.file_name + ".0.iir")
        try:
            sdfg.compile(optimizer="")
        except:
            compiled = False
        else:
            compiled = True
        self.assertTrue(compiled)
        

class coriolis(LegalSDFG, unittest.TestCase):
    file_name = "coriolis"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo = 1
        u = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        v = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        fc = numpy.arange(I*J).astype(dace.float64.type).reshape(I,J)

        u_tens = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        v_tens = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        expected_u = numpy.copy(u_tens)
        expected_v = numpy.copy(v_tens)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                # u_tens += 0.25 * (fc * (v + v[i+1]) + fc[j-1] * (v[j-1] + v[i+1,j-1]));
                expected_u[i,j,:] += 0.25 * (fc[i,j] * (v[i,j,:] + v[i+1,j,:]) + fc[i,j-1] * (v[i,j-1,:] + v[i+1,j-1,:]))
                # v_tens -= 0.25 * (fc * (u + u[j+1]) + fc[i-1] * (u[i-1] + u[i-1,j+1]));
                expected_v[i,j,:] -= 0.25 * (fc[i,j] * (u[i,j,:] + u[i,j+1,:]) + fc[i-1,j] * (u[i-1,j,:] + u[i-1,j+1,:]))

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            u_tens = u_tens,
            v_tens = v_tens,
            u = u,
            v = v,
            fc = fc,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertTrue((expected_u == u_tens).all(), "Expected:\n{}\nReceived:\n{}".format(expected_u, u_tens))
        self.assertTrue((expected_v == v_tens).all(), "Expected:\n{}\nReceived:\n{}".format(expected_v, v_tens))
        

class thomas(LegalSDFG, unittest.TestCase):
    file_name = "thomas"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo = 0
        a = numpy.arange(0,0+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        b = numpy.arange(1,1+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        c = numpy.arange(5,5+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        d = numpy.arange(9,9+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        data = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)

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
                    d[i,j,k] = d[i,j,k] - (d[i,j,k-1] * a[i,j,k]) * divided

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

        expected = numpy.copy(data)
        data = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            acol = a,
            bcol = b,
            ccol = c,
            dcol = d,
            datacol = data,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertTrue((expected == data).all(), "Expected:\n{}\nReceived:\n{}".format(expected, data))


# class horizontal_diffusion(LegalSDFG, unittest.TestCase):
#     file_name = "horizontal_diffusion"

#     def test_4_numerically(self):
#         sdfg = get_sdfg(self.file_name + ".0.iir")
#         sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
#         sdfg = sdfg.compile(optimizer="")


# class vertical_advection(LegalSDFG, unittest.TestCase):
#     file_name = "vertical_advection"

#     def test_4_numerically(self):
#         sdfg = get_sdfg(self.file_name + ".0.iir")
#         sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
#         sdfg = sdfg.compile(optimizer="")


if __name__ == '__main__':
    unittest.main()
    