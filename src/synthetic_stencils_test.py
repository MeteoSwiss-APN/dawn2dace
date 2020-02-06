from test_helpers import *

class set_zero(LegalSDFG, Asserts):
    file_name = "set_zero"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        output = Iota(I,J,K)
        output_dace = numpy.copy(output)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = 0

        output = Transpose(output)
        output_dace = Transpose(output_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)


class copy(LegalSDFG, Asserts):
    file_name = "copy"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        original = Iota(I,J,K)
        copy = Zeros(I,J,K)
        copy_dace = numpy.copy(copy)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    copy[i,j,k] = original[i,j,k]

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
        I,J,K = 4,4,4
        halo = 1
        original = Iota(I,J,K)
        copy = Zeros(I,J,K)
        copy_dace = numpy.copy(copy)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    copy[i,j,k] = original[i,j,k]

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

class const_value(LegalSDFG, Asserts):
    file_name = "const_value"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        input = Iota(I,J,K)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        # vertical_region(k_start, k_end) {
        #   const double tmp = 10.0 / 5.0;
        #   output = input + tmp;
        # }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = input[i,j,k] + 2.0

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

class const_array(LegalSDFG, Asserts):
    file_name = "const_array"

    def test_3_numerically(self):
        I,J,K = 6,6,6
        halo = 2
        input = Iota(I,J,K)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        # vertical_region(k_start, k_end) {
        #   const double cf[5] = {-1.0, -2.0, 10.0, -3.0, -2.0};
        
        #   output = cf[0] * input[i-2]
        #          + cf[1] * input[i-1]
        #          + cf[2] * input
        #          + cf[3] * input[i+1]
        #          + cf[4] * input[i+2];
        # }
        cf = (-1.0, -2.0, 10.0, -3.0, -2.0)
        
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i, j, k] = cf[0] * input[i-2, j, k] + \
                                      cf[1] * input[i-1, j, k] + \
                                      cf[2] * input[i+0, j, k] + \
                                      cf[3] * input[i+1, j, k] + \
                                      cf[4] * input[i+2, j, k]

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

class i_storage(LegalSDFG, Asserts):
    file_name = "i_storage"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        fill = numpy.arange(I).astype(dace.float64.type).reshape(I)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = fill[i]

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        output = Transpose(output)
        output_dace = Transpose(output_dace)

        sdfg(
            fill = fill,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)

class j_storage(LegalSDFG, Asserts):
    file_name = "j_storage"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        fill = numpy.arange(J).astype(dace.float64.type).reshape(J)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = fill[j]

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        output = Transpose(output)
        output_dace = Transpose(output_dace)

        sdfg(
            fill = fill,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)

class k_storage(LegalSDFG, Asserts):
    file_name = "k_storage"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        fill = numpy.arange(K).astype(dace.float64.type).reshape(K)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = fill[k]

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        output = Transpose(output)
        output_dace = Transpose(output_dace)

        sdfg(
            fill = fill,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)

class ij_storage(LegalSDFG, Asserts):
    file_name = "ij_storage"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        fill = Iota(I,J)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = fill[i,j]

        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        fill = Transpose(fill)
        output = Transpose(output)
        output_dace = Transpose(output_dace)

        sdfg(
            fill = fill,
            output = output_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(output, output_dace)


class inout_variable(LegalSDFG, Asserts):
    file_name = "inout_variable"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        a = Zeros(I,J,K)
        a_dace = numpy.copy(a)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    a[i,j,k] = a[i,j,k] + 7
        
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
        I,J,K = 4,4,4
        halo = 1
        a = Zeros(I,J,K)
        b = Iota(I,J,K)
        c = Iota(I,J,K, offset=100)
        a_dace = numpy.copy(a)

        # vertical_region(k_start, k_end) { a = b[i-1] + b[j+1] + b[i+1, j-1] + c[i-1]; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    a[i, j, k] = b[i-1, j, k] + b[i, j+1, k] + b[i+1, j-1, k] + c[i-1, j, k]
        
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


class horizontal_temp_offsets(LegalSDFG, Asserts):
    file_name = "horizontal_temp_offsets"

    def test_3_numerically(self):
        I,J,K = 4,4,3
        halo = 1
        input = Iota(I,J,K)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        # vertical_region(k_start+1, k_end) {
        #     tmp = input;
        #     output = tmp[k-1];
        # }

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = input[i-1,j,k]

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


class vertical_offsets(LegalSDFG, Asserts):
    file_name = "vertical_offsets"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        input = Iota(I,J,K)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        # vertical_region(k_start, k_start) { output = input[k+1] }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                output[i, j, 0] = input[i, j, 1]

        # vertical_region(k_start + 1, k_end) { output = input[k-1]; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(1, K):
                    output[i, j, k] = input[i, j, k-1]

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

class parametric_offsets(LegalSDFG, Asserts):
    file_name = "parametric_offsets"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 1
        support = Iota(I,J,K)
        interpolation = Zeros(I,J,K)
        interpolation_dace = numpy.copy(interpolation)

        # stencil_function avg {
        #     offset off;
        #     storage in;

        #     Do { return 0.5 * (in[off] + in); }
        # };

        # vertical_region(k_start, k_start) { interpolation = avg(i - 1, support) + avg(j + 1, support); }

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    interpolation[i,j,k] = (0.5 * (support[i-1,j,k] + support[i,j,k])) + (0.5 * (support[i,j+1,k] + support[i,j,k]))

        support = Transpose(support)
        interpolation = Transpose(interpolation)
        interpolation_dace = Transpose(interpolation_dace)
        
        sdfg = get_sdfg(self.file_name + ".0.iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg = sdfg.compile(optimizer="")

        sdfg(
            support = support,
            interpolation = interpolation_dace,
            I = numpy.int32(I),
            J = numpy.int32(J),
            K = numpy.int32(K),
            halo = numpy.int32(halo))

        self.assertEqual(interpolation, interpolation_dace)

class vertical_specification_1(LegalSDFG, Asserts):
    file_name = "vertical_specification_1"

    def test_3_numerically(self):
        I,J,K = 4,4,4
        halo = 0
        input1 = Iota(I,J,K)
        input2 = Iota(I,J,K, offset=100)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        output = Zeros(I,J,K)
        # vertical_region(k_start, k_end-1) { output = input1; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K-1):
                    output[i, j, k] = input1[i, j, k]

        # vertical_region(k_start+1, k_end) { output = input2; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(1, K):
                    output[i, j, k] = input2[i, j, k]

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
        input1 = Iota(I,J,K)
        input2 = Iota(I,J,K, offset=100)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        # vertical_region(k_start+1, k_end) { output = input2; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(1, K):
                    output[i, j, k] = input2[i, j, k]

        # vertical_region(k_start, k_end-1) { output = input1; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K-1):
                    output[i, j, k] = input1[i, j, k]

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
        I,J,K = 4,4,4
        halo = 0
        input = Iota(I,J,K)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = input[i,j,k] + 5

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
        I,J,K = 4,4,4
        halo = 0
        input = Iota(I,J,K)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = input[i,j,k] + 5

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
        I,J,K = 4,4,4
        halo = 0
        input = Iota(I,J,K)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = input[i,j,k] + 3.14

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
        I,J,K = 4,4,4
        halo = 0
        input = Iota(I,J,K)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)
        
        # vertical_region(k_start, k_end) { output = input+ 3.14; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = input[i,j,k] + 3.14

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
        I,J,K = 4,4,4
        halo = 0
        input = Iota(I,J,K)
        output = Zeros(I,J,K)
        output_dace = numpy.copy(output)

        # output = 0.25 * (input + 7);
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    output[i,j,k] = 0.25 * (input[i,j,k] + 7)

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
        I,J,K = 4,4,4
        halo = 0
        a = Iota(I,J,K)
        a_dace = numpy.copy(a)

        # vertical_region(k_start+1, k_end) { a += a[k-1]; }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(1, K):
                    a[i,j,k] += a[i,j,k-1]

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
        I,J,K = 4,4,4
        halo = 0
        x = Iota(I,J,K)
        y = Zeros(I,J,K)
        y_dace = numpy.copy(y)

        # vertical_region(k_start, k_end) { y = min(10.0, max(5.0, x)); }
        for i in range(halo, I-halo):
            for j in range(halo, J-halo):
                for k in range(0, K):
                    y[i,j,k] = min(10.0, max(5.0, x[i,j,k]))

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
        I,J,K = 4,4,4
        halo = 0
        a = Iota(I,J,K, offset=0)
        b = Iota(I,J,K, offset=1)
        c = Iota(I,J,K, offset=5)
        d = Iota(I,J,K, offset=9)
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
    