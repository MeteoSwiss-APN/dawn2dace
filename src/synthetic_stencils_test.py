from test_helpers import *

class copy(LegalSDFG, Asserts):
    file_name = "copy"

    def test_3_numerically(self):
        I,J,K = 6,6,6
        halo = 0
        original = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        copy = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        copy_dace = numpy.copy(copy)

        copy = numpy.copy(original)

        original = Transpose(original)
        copy = Transpose(copy)
        copy_dace = Transpose(copy_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            original = original,
            copy = copy_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(copy, copy_dace)

class copy_with_halo(LegalSDFG, Asserts):
    file_name = "copy"

    def test_3_numerically(self):
        I,J,K = 3,4,6
        halo = 1
        original = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        copy = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        copy_dace = numpy.copy(copy)

        copy[halo:I-halo, halo:J-halo, :] = original[halo:I-halo, halo:J-halo, :]

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        original = Transpose(original)
        copy = Transpose(copy)
        copy_dace = Transpose(copy_dace)

        sdfg(
            original = original,
            copy = copy_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(copy, copy_dace)


class inout_variable(LegalSDFG, Asserts):
    file_name = "inout_variable"

    def test_3_numerically(self):
        I,J,K = 6,6,6
        halo = 0
        a = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        a_dace = numpy.copy(a)

        a = a + 7
        
        a = Transpose(a)
        a_dace = Transpose(a_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            a = a_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(a, a_dace)


class horizontal_offsets(LegalSDFG, Asserts):
    file_name = "horizontal_offsets"

    def test_3_numerically(self):
        I,J,K = 6,6,6
        halo = 1
        a = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        b = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        c = numpy.arange(100,100+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        a_dace = numpy.copy(a)

        # vertical_region(k_start, k_end) { a = b[i-1] + b[j+1] + b[i+1, j-1] + c[i-1]; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                    a[i, j, :] = b[i-1, j, :] + b[i, j+1, :] + b[i+1, j-1, :] + c[i-1, j, :]
        
        a = Transpose(a)
        b = Transpose(b)
        c = Transpose(c)
        a_dace = Transpose(a_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            a = a_dace,
            b = b,
            c = c,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(a, a_dace)



class vertical_offsets(LegalSDFG, Asserts):
    file_name = "vertical_offsets"

    def test_3_numerically(self):
        I,J,K = 6,6,6
        halo = 0
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        output_dace = numpy.copy(output)

        # vertical_region(k_start, k_start) { output = input[k+1] }
        output[:, :, 0] = input[:, :, 1]

        # vertical_region(k_start + 1, k_end) { output = input[k-1]; }
        for k in range(1, K):
            output[:, :, k] = input[:, :, k-1]

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)

class vertical_specification_1(LegalSDFG, Asserts):
    file_name = "vertical_specification_1"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        input1 = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        input2 = numpy.arange(100, I*J*K+100).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        output_dace = numpy.copy(output)

        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        # vertical_region(k_start, k_end-1) { output = input1; }
        for k in range(0, K-1):
            output[:, :, k] = input1[:, :, k]

        # vertical_region(k_start+1, k_end) { output = input2; }
        for k in range(1, K):
            output[:, :, k] = input2[:, :, k]

        input1 = Transpose(input1)
        input2 = Transpose(input2)
        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input1 = input1,
            input2 = input2,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)


class vertical_specification_2(LegalSDFG, Asserts):
    file_name = "vertical_specification_2"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        input1 = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        input2 = numpy.arange(100, I*J*K+100).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        output_dace = numpy.copy(output)

        # vertical_region(k_start+1, k_end) { output = input2; }
        for k in range(1, K):
            output[:, :, k] = input2[:, :, k]

        # vertical_region(k_start, k_end-1) { output = input1; }
        for k in range(0, K-1):
            output[:, :, k] = input1[:, :, k]

        input1 = Transpose(input1)
        input2 = Transpose(input2)
        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input1 = input1,
            input2 = input2,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)


class scope_in_region(LegalSDFG, Asserts):
    file_name = "scope_in_region"

    def test_3_numerically(self):
        I,J,K = 6,6,6
        halo = 0
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        output_dace = numpy.copy(output)

        output = input + 5

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)


class scope_in_stencil(LegalSDFG, Asserts):
    file_name = "scope_in_stencil"

    def test_3_numerically(self):
        I,J,K = 6,6,6
        halo = 0
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        output_dace = numpy.copy(output)

        output = input + 5

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)


class scope_in_global(LegalSDFG, Asserts):
    file_name = "scope_in_global"

    def test_3_numerically(self):
        I,J,K = 6,6,6
        halo = 0
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        output_dace = numpy.copy(output)

        output = input + 3.14

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)


class scopes_mixed(LegalSDFG, Asserts):
    file_name = "scopes_mixed"

    def test_3_numerically(self):
        I,J,K = 6,6,6
        halo = 0
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        output_dace = numpy.copy(output)
        
        # vertical_region(k_start, k_end) { output = input+ 3.14; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i, j, k] = input[i, j, k] + 3.14

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)


class brackets(LegalSDFG, Asserts):
    file_name = "brackets"

    def test_3_numerically(self):
        I,J,K = 6,6,6
        halo = 0
        input = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        output = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        output_dace = numpy.copy(output)

        # output = 0.25 * (input + 7);
        output = 0.25 * (input + 7)

        input = Transpose(input)
        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            input = input,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)


class loop(LegalSDFG, Asserts):
    file_name = "loop"

    def test_3_numerically(self):
        I,J,K = 3,3,3
        halo = 0
        a = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        a_dace = numpy.copy(a)

        # vertical_region(k_start+1, k_end) { a += a[k-1]; }
        for k in range(1, K):
            a[:,:,k] += a[:,:,k-1]

        a = Transpose(a)
        a_dace = Transpose(a_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            a = a_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(a, a_dace)


class mathfunctions(LegalSDFG, Asserts):
    file_name = "mathfunctions"

    def test_3_numerically(self):
        I,J,K = 3,3,3
        halo = 0
        x = numpy.arange(I*J*K).astype(dace.float64.type).reshape(I,J,K)
        y = numpy.zeros(shape=(I,J,K), dtype=dace.float64.type)
        y_dace = numpy.copy(x)

        # vertical_region(k_start, k_end) { y = min(5.0, max(10.0, x)); }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    y[i,j,k] += min(5.0, max(10.0, x[i,j,k]))

        x = Transpose(x)
        y = Transpose(y)
        y_dace = Transpose(y_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            x = x,
            y = y_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(y, y_dace)


class tridiagonal_solve(LegalSDFG, Asserts):
    file_name = "tridiagonal_solve"

    def test_3_numerically(self):
        I,J,K = 3,3,3
        halo = 0
        a = numpy.arange(0,0+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        b = numpy.arange(1,1+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        c = numpy.arange(5,5+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        d = numpy.arange(9,9+I*J*K).astype(dace.float64.type).reshape(I,J,K)
        a_dace = numpy.copy(a)
        b_dace = numpy.copy(b)
        c_dace = numpy.copy(c)
        d_dace = numpy.copy(d)
        
        # vertical_region(k_start, k_start) {
        #     c = c / b;
        #     d = d / b;
        # }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, 1):
                    c[i,j,k] = c[i,j,k] / b[i,j,k]
                    d[i,j,k] = d[i,j,k] / b[i,j,k]

        # vertical_region(k_start + 1, k_end) {
        #     double m = 1.0 / (b - a * c[k - 1]);
        #     c = c * m;
        #     d = (d - a * d[k - 1]) * m;
        # }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(1, K):
                    m = 1.0 / (b[i,j,k] - a[i,j,k] * c[i,j,k-1])
                    c[i,j,k] = c[i,j,k] * m
                    d[i,j,k] = (d[i,j,k] - a[i,j,k] * d[i,j,k-1]) * m

        # vertical_region(k_end - 1, k_start) {
        #     d -= c * d[k + 1];
        # }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in reversed(range(0, K-1)):
                    d[i,j,k] -= c[i,j,k] * d[i,j,k+1]

        a = Transpose(a)
        b = Transpose(b)
        c = Transpose(c)
        d = Transpose(d)
        a_dace = Transpose(a_dace)
        b_dace = Transpose(b_dace)
        c_dace = Transpose(c_dace)
        d_dace = Transpose(d_dace)

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            a = a_dace,
            b = b_dace,
            c = c_dace,
            d = d_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertIsClose(a, a_dace)
        self.assertIsClose(b, b_dace)
        self.assertIsClose(c, c_dace)
        self.assertIsClose(d, d_dace)


if __name__ == '__main__':
    unittest.main()
    