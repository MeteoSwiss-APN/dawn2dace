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
        self.assertIsNotNone(read_file(self.file_name))

    def test_2_sdfg_is_valid(self):
        sdfg = get_sdfg(self.file_name)
        self.assertTrue(sdfg.is_valid())
        
    def test_3_sdfg_compiles(self):
        sdfg = get_sdfg(self.file_name)
        try:
            sdfg.compile(optimizer="")
        except:
            compiled = False
        else:
            compiled = True
        self.assertTrue(compiled)
        

class coriolis(LegalSDFG, unittest.TestCase):
    file_name = "coriolis.0.iir"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 1
        u = numpy.ones(shape=(J,K,I), dtype=dace.float64.type) #numpy.arange(J*K*I).astype(dace.float64.type).reshape(J,K,I)
        v = numpy.ones(shape=(J,K,I), dtype=dace.float64.type) #numpy.arange(J*K*I).astype(dace.float64.type).reshape(J,K,I)
        fc = numpy.ones(shape=(J,I), dtype=dace.float64.type) #numpy.arange(J*I).astype(dace.float64.type).reshape(J,I)

        u_tens = numpy.zeros(shape=(J,K,I), dtype=dace.float64.type)
        v_tens = numpy.zeros(shape=(J,K,I), dtype=dace.float64.type)
        expected_u = numpy.zeros(shape=(J,K,I), dtype=dace.float64.type)
        expected_v = numpy.zeros(shape=(J,K,I), dtype=dace.float64.type)

        for i in range(halo_size, I-halo_size):
            for j in range(halo_size, J-halo_size):
                for k in range(0, K):
                    # u_tens += 0.25 * (fc * (v + v[i + 1]) + fc[j - 1] * (v[j - 1] + v[i + 1, j - 1]));
                    expected_u[j,k,i] += 0.25 * (fc[j,i] * (v[j,k,i] + v[j,k,i+1]) + fc[j-1,i] * (v[j-1,k,i] + v[j-1,k,i+1]))
                    # v_tens -= 0.25 * (fc * (u + u[j + 1]) + fc[i - 1] * (u[i - 1] + u[i - 1, j + 1]));
                    expected_v[j,k,i] -= 0.25 * (fc[j,i] * (u[j,k,i] + u[j+1,k,i]) + fc[j,i-1] * (u[j,k,i-1] + u[j+1,k,i-1]))

        sdfg = get_sdfg(self.file_name)
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            u_tens_t = u_tens,
            v_tens_t = v_tens,
            u_t = u,
            v_t = v,
            fc_t = fc,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((expected_u == u_tens).all(), "Expected:\n{}\nReceived:\n{}".format(expected_u, u_tens))
        self.assertTrue((expected_v == v_tens).all(), "Expected:\n{}\nReceived:\n{}".format(expected_v, v_tens))
        

class thomas(LegalSDFG, unittest.TestCase):
    file_name = "thomas.0.iir"

if __name__ == '__main__':
    unittest.main()
    