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


class copy(LegalSDFG, unittest.TestCase):
    file_name = "copy"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 0
        original = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        copy = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            original = original,
            copy = copy,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((copy == original).all(), "Expected:\n{}\nReceived:\n{}".format(original, copy))

class copy_with_halo(LegalSDFG, unittest.TestCase):
    file_name = "copy"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 1
        original = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        copy = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)

        expected = numpy.copy(copy)
        expected[halo_size:I-halo_size, halo_size:J-halo_size, :] = original[halo_size:I-halo_size, halo_size:J-halo_size, :]

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            original = original,
            copy = copy,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((copy == expected).all(), "Expected:\n{}\nReceived:\n{}".format(expected, copy))


class inout_variable(LegalSDFG, unittest.TestCase):
    file_name = "inout_variable"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 0
        a = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        expected = a + 7
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            a = a,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((a == expected).all(), "Expected:\n{}\nReceived:\n{}".format(expected, a))


class horizontal_offsets(LegalSDFG, unittest.TestCase):
    file_name = "horizontal_offsets"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 1
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)

        expected = numpy.copy(output)
        for i in range(halo_size, I-halo_size):
            for j in range(halo_size, J-halo_size):
                    # a = b[i-1] + b[j+1] + b[i+1, j-1];
                    expected[i, j, :] = input[i-1, j, :] + input[i, j+1, :] + input[i+1, j-1, :]
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            b = input,
            a = output,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((output == expected).all(), "Expected:\n{}\nReceived:\n{}".format(expected, output))



class vertical_offsets(LegalSDFG, unittest.TestCase):
    file_name = "vertical_offsets"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 0
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)

        expected = numpy.copy(output)

        # vertical_region(k_start, k_start) { output = input[k+1] }
        expected[:, :, 0] = input[:, :, 1]

        # vertical_region(k_start + 1, k_end) { output = input[k-1]; }
        for k in range(1, K):
            expected[:, :, k] = input[:, :, k-1]
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((output == expected).all(), "Expected:\n{}\nReceived:\n{}".format(expected, output))

class vertical_specification_1(LegalSDFG, unittest.TestCase):
    file_name = "vertical_specification_1"

    def test_4_numerically(self):
        I,J,K = 4,4,4
        halo_size = 0
        input1 = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        input2 = numpy.arange(100, I*J*K+100).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)

        expected = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        # vertical_region(k_start, k_end-1) { output = input1; }
        for k in range(0, K-1):
            expected[:, :, k] = input1[:, :, k]

        # vertical_region(k_start+1, k_end) { output = input2; }
        for k in range(1, K):
            expected[:, :, k] = input2[:, :, k]
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input1 = input1,
            input2 = input2,
            output = output,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((output == expected).all(), "Expected:\n{}\nReceived:\n{}".format(expected, output))


class vertical_specification_2(LegalSDFG, unittest.TestCase):
    file_name = "vertical_specification_2"

    def test_4_numerically(self):
        I,J,K = 4,4,4
        halo_size = 0
        input1 = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        input2 = numpy.arange(100, I*J*K+100).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)

        expected = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        # vertical_region(k_start+1, k_end) { output = input2; }
        for k in range(1, K):
            expected[:, :, k] = input2[:, :, k]

        # vertical_region(k_start, k_end-1) { output = input1; }
        for k in range(0, K-1):
            expected[:, :, k] = input1[:, :, k]
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input1 = input1,
            input2 = input2,
            output = output,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((output == expected).all(), "Expected:\n{}\nReceived:\n{}".format(expected, output))


class scope_in_region(LegalSDFG, unittest.TestCase):
    file_name = "scope_in_region"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 0
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)

        expected = input + 5
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((output == expected).all(), "Expected:\n{}\nReceived:\n{}".format(expected, output))


class scope_in_stencil(LegalSDFG, unittest.TestCase):
    file_name = "scope_in_stencil"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 0
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)

        expected = input + 5
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((output == expected).all(), "Expected:\n{}\nReceived:\n{}".format(expected, output))


class scopes_mixed(LegalSDFG, unittest.TestCase):
    file_name = "scopes_mixed"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 1
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        
        expected = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        # vertical_region(k_start, k_start) { output = input[i-1] + 3.14; }
        for i in range(halo_size, I-halo_size):
            expected[i, :, 0] = input[i-1, :, 0] + 3.14

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            data_in = input,
            data_out = output,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((input == output).all(), "Expected:\n{}\nReceived:\n{}".format(input, output))


class brackets(LegalSDFG, unittest.TestCase):
    file_name = "brackets"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 0
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)

        # output = 0.25 * (input + 7);
        expected = 0.25 * (input + 7)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        self.assertTrue((output == expected).all(), "Expected:\n{}\nReceived:\n{}".format(expected, output))


class tridiagonal_solve(LegalSDFG, unittest.TestCase):
    file_name = "tridiagonal_solve"

    def test_4_numerically(self):
        I,J,K = 3,3,3
        halo_size = 0
        a = numpy.random.rand(I,J,K).astype(dace.float64.type)
        b = numpy.random.rand(I,J,K).astype(dace.float64.type)
        c = numpy.random.rand(I,J,K).astype(dace.float64.type)
        d = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            a = a,
            b = b,
            c = c,
            d = d,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo_size = numpy.int32(halo_size))

        # self.assertTrue((output == expected).all(), "Expected:\n{}\nReceived:\n{}".format(expected, output))


if __name__ == '__main__':
    unittest.main()
    