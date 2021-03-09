from test_helpers import *
from dace.transformation.interstate import StateFusion, InlineSDFG
from dace.transformation.dataflow import *

class set_zero(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        output = Iota(dim.ijk)
        output_dace = Iota(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = 0
        
        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class duplicate(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([1,2,4], [1,2,5], 'ijk', halo=0)
        original = Iota(dim.ijk)
        copy = Zeros(dim.ijk)
        copy_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    copy[i,j,k] = original[i,j,k]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            original = original,
            copy = copy_dace,
            **dim.ProgramArguments())

        self.assertEqual(copy, copy_dace)

class copy_with_halo(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=1)
        
        original = Iota(dim.ijk)
        copy = Zeros(dim.ijk)
        copy_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    copy[i,j,k] = original[i,j,k]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            original = original,
            copy = copy_dace,
            **dim.ProgramArguments())

        self.assertEqual(copy, copy_dace)

# class staggered_k(LegalSDFG, Asserts):
#     def test_3_numerically(self):
#         dim = Dimensions([4,4,4], [4,4,7], 'ijk', halo=0)
#         data = Iota(dim.ijk)
#         mid_avg = Zeros(dim.ijk)
#         mid_avg_dace = Zeros(dim.ijk)

#         for i in range(dim.halo, dim.I-dim.halo):
#             for j in range(dim.halo, dim.J-dim.halo):
#                 for k in range(0, dim.K):
#                     mid_avg[i,j,k] = data[i,j,k] + data[i,j,k+1]
        
#         sdfg = get_sdfg(self.__class__.__name__ + ".iir")
#         sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
#         sdfg.expand_library_nodes()
#         sdfg.apply_strict_transformations(validate=False)
#         sdfg.apply_transformations_repeated([InlineSDFG])
#         sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
#         sdfg = sdfg.compile()

#         sdfg(
#             data = data,
#             mid_avg = mid_avg_dace,
#             **dim.ProgramArguments())

#         self.assertEqual(mid_avg, mid_avg_dace)

class delta(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        inp = Iota(dim.ijk)
        out = Zeros(dim.ijk)
        out_dace = Zeros(dim.ijk)

        # vertical_region(k_start + 1, k_end - 1) { out = 0.5 * d(k - 1, inp) + 2.0 * d(k + 1, inp); }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(1, dim.K-1):
                    out[i,j,k] = 0.5 * (inp[i,j,k-1] - inp[i,j,k]) + 2.0 * (inp[i,j,k+1] - inp[i,j,k])

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            inp = inp,
            out = out_dace,
            **dim.ProgramArguments())

        self.assertEqual(out, out_dace)

class const_value(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        input = Iota(dim.ijk)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        # vertical_region(k_start, k_end) {
        #   const double tmp = 10.0 / 5.0;
        #   output = input + tmp;
        # }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = input[i,j,k] + 2.0

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class i_storage(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        fill = Iota(dim.i)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = fill[i]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            fill = fill,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class j_storage(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        fill = Iota(dim.j)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = fill[j]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            fill = fill,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class k_storage(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        fill = Iota(dim.k)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = fill[k]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            fill = fill,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class ij_storage(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        fill = Iota(dim.ij)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = fill[i,j]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            fill = fill,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class inout_variable(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        a = Zeros(dim.ijk)
        a_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    a[i,j,k] = a[i,j,k] + 7
        
        
        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            a = a_dace,
            **dim.ProgramArguments())

        self.assertEqual(a, a_dace)

class horizontal_offsets(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=1)
        a = Zeros(dim.ijk)
        b = Iota(dim.ijk)
        c = Iota(dim.ijk, offset=100)
        a_dace = Zeros(dim.ijk)

        # vertical_region(k_start, k_end) { a = b[i-1] + b[j+1] + b[i+1, j-1] + c[i-1]; }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    a[i, j, k] = b[i-1, j, k] + b[i, j+1, k] + b[i+1, j-1, k] + c[i-1, j, k]
        
        
        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            a = a_dace,
            b = b,
            c = c,
            **dim.ProgramArguments())

        self.assertEqual(a, a_dace)

class horizontal_temp_offsets(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=1)
        input = Iota(dim.ijk)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        # vertical_region(k_start+1, k_end) {
        #     tmp = input;
        #     output = tmp[k-1];
        # }

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = input[i-1,j,k]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class vertical_offsets(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        input = Iota(dim.ijk)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        # vertical_region(k_start, k_start) { output = input[k+1] }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                output[i, j, 0] = input[i, j, 1]

        # vertical_region(k_start + 1, k_end) { output = input[k-1]; }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(1, dim.K):
                    output[i, j, k] = input[i, j, k-1]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class parametric_offsets(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=1)
        support = Iota(dim.ijk)
        interpolation = Zeros(dim.ijk)
        interpolation_dace = Zeros(dim.ijk)

        # stencil_function avg {
        #     offset off;
        #     storage in;
        #     Do { return 0.5 * (in[off] + in); }
        # };
        # vertical_region(k_start, k_start) { interpolation = avg(i - 1, support) + avg(j + 1, support); }

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    interpolation[i,j,k] = (0.5 * (support[i-1,j,k] + support[i,j,k])) + (0.5 * (support[i,j+1,k] + support[i,j,k]))

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            support = support,
            interpolation = interpolation_dace,
            **dim.ProgramArguments())

        self.assertEqual(interpolation, interpolation_dace)

class vertical_specification_1(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        input1 = Iota(dim.ijk)
        input2 = Iota(dim.ijk, offset=100)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        output = Zeros(dim.ijk)
        # vertical_region(k_start, k_end-1) { output = input1; }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K-1):
                    output[i, j, k] = input1[i, j, k]

        # vertical_region(k_start+1, k_end) { output = input2; }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(1, dim.K):
                    output[i, j, k] = input2[i, j, k]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input1 = input1,
            input2 = input2,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class vertical_specification_2(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        input1 = Iota(dim.ijk)
        input2 = Iota(dim.ijk, offset=100)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        # vertical_region(k_start, k_end-1) { output = input1; }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K-1):
                    output[i, j, k] = input1[i, j, k]

        # vertical_region(k_start+1, k_end) { output = input2; }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(1, dim.K):
                    output[i, j, k] = input2[i, j, k]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input1 = input1,
            input2 = input2,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class scope_in_region(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        input = Iota(dim.ijk)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = input[i,j,k] + 5

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class scope_in_stencil(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        input = Iota(dim.ijk)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = input[i,j,k] + 5

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class scope_in_global(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        input = Iota(dim.ijk)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = input[i,j,k] + 3.14

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments(),
            global_var=3.14)

        self.assertEqual(output, output_dace)

class scopes_mixed(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        input = Iota(dim.ijk)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)
        
        # vertical_region(k_start, k_end) { output = input+ 3.14; }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = input[i,j,k] + 3.14

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments(),
            global_var=3.14)

        self.assertEqual(output, output_dace)

class brackets(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        input = Iota(dim.ijk)
        output = Zeros(dim.ijk)
        output_dace = Zeros(dim.ijk)

        # output = 0.25 * (input + 7);
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    output[i,j,k] = 0.25 * (input[i,j,k] + 7)
        
        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            input = input,
            output = output_dace,
            **dim.ProgramArguments())

        self.assertEqual(output, output_dace)

class loop(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        a = Iota(dim.ijk)
        a_dace = Iota(dim.ijk)

        # vertical_region(k_start+1, k_end) { a += a[k-1]; }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(1, dim.K):
                    a[i,j,k] += a[i,j,k-1]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            a = a_dace,
            **dim.ProgramArguments())

        self.assertEqual(a, a_dace)

class mathfunctions(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        a = Iota(dim.ijk)
        b = Zeros(dim.ijk)
        b_dace = Zeros(dim.ijk)

        # vertical_region(k_start, k_end) { b = min(10.0, max(5.0, a)); }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, dim.K):
                    b[i,j,k] = min(10.0, max(5.0, a[i,j,k]))

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            a = a,
            b = b_dace,
            **dim.ProgramArguments())

        self.assertEqual(b, b_dace)

class tridiagonal_solve(LegalSDFG, Asserts):
    def test_3_numerically(self):
        dim = Dimensions([4,4,4], [4,4,5], 'ijk', halo=0)
        a = Iota(dim.ijk, offset=0)
        b = Iota(dim.ijk, offset=1)
        c = Iota(dim.ijk, offset=5)
        d = Iota(dim.ijk, offset=9)
        a_dace = Iota(dim.ijk, offset=0)
        b_dace = Iota(dim.ijk, offset=1)
        c_dace = Iota(dim.ijk, offset=5)
        d_dace = Iota(dim.ijk, offset=9)
        
        # vertical_region(k_start, k_start) {
        #     c = c / b;
        #     d = d / b;
        # }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(0, 1):
                    c[i,j,k] = c[i,j,k] / b[i,j,k]
                    d[i,j,k] = d[i,j,k] / b[i,j,k]

        # vertical_region(k_start + 1, k_end) {
        #     double m = 1.0 / (b - a * c[k - 1]);
        #     c = c * m;
        #     d = (d - a * d[k - 1]) * m;
        # }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in range(1, dim.K):
                    m = 1.0 / (b[i,j,k] - a[i,j,k] * c[i,j,k-1])
                    c[i,j,k] = c[i,j,k] * m
                    d[i,j,k] = (d[i,j,k] - a[i,j,k] * d[i,j,k-1]) * m

        # vertical_region(k_end - 1, k_start) {
        #     d -= c * d[k + 1];
        # }
        for i in range(dim.halo, dim.I-dim.halo):
            for j in range(dim.halo, dim.J-dim.halo):
                for k in reversed(range(0, dim.K-1)):
                    d[i,j,k] -= c[i,j,k] * d[i,j,k+1]

        sdfg = get_sdfg(self.__class__.__name__ + ".iir")
        sdfg.save("gen/" + self.__class__.__name__ + ".sdfg")
        sdfg.expand_library_nodes()
        sdfg.apply_strict_transformations(validate=False)
        sdfg.apply_transformations_repeated([InlineSDFG])
        sdfg.save("gen/" + self.__class__.__name__ + "_expanded.sdfg")
        sdfg = sdfg.compile()

        sdfg(
            a = a_dace,
            b = b_dace,
            c = c_dace,
            d = d_dace,
            **dim.ProgramArguments())

        self.assertIsClose(a, a_dace)
        self.assertIsClose(b, b_dace)
        self.assertIsClose(c, c_dace)
        self.assertIsClose(d, d_dace)

if __name__ == '__main__':
    unittest.main()
    