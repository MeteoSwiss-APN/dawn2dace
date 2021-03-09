import unittest
from helpers import *
from itertools import permutations

class Pairwise(unittest.TestCase):
    def test_list_of_0(self):
        pw = list(pairwise([]))
        self.assertEqual(pw, [])

    def test_list_of_1(self):
        pw = list(pairwise([1]))
        self.assertEqual(pw, [])

    def test_list_of_2(self):
        pw = list(pairwise([1,2]))
        self.assertEqual(pw, [(1,2)])
    
    def test_list_of_3(self):
        pw = list(pairwise([1,2,3]))
        self.assertEqual(pw, [(1,2), (2,3)])


class SymbolicSum(unittest.TestCase):
    def test_positive_symbol(self):
        sym = Symbol('halo')
        self.assertEqual(str(Symbol('halo')), 'halo')

    def test_negative_symbol(self):
        sym = -Symbol('halo')
        self.assertEqual(str(sym), '-halo')

    def test_two_symbols(self):
        sym = Symbol('I') - Symbol('J')
        self.assertEqual(str(-sym), '-I+J')

    def test_two_numbers(self):
        sym = Symbol('I') + 1 - 1
        self.assertEqual(str(-sym), '-I')

    def test_sum(self):
        sym = Symbol('halo') + 1
        self.assertEqual(str(sym), 'halo+1')
        self.assertEqual(str(-sym), '-halo-1')

    def test_partial_Eval(self):
        sym = Symbol('I') + Symbol('J') + 1
        sym = sym.Eval('I', 10)
        self.assertEqual(str(sym), 'J+11')

    def test_full_Eval(self):
        sym = Symbol('I') + Symbol('J') + 1
        sym = sym.Eval('I', 10).Eval('J', -1)
        self.assertTrue(sym.IsInteger())
        self.assertEqual(sym.integer, 10)


class Bool3D_test(unittest.TestCase):
    def test_or(self):
        b = Bool3D.Or([Bool3D(True,False,False), Bool3D(False,True,False)])
        self.assertEqual(b, Bool3D(True,True,False))

class HalfOpenInterval_test(unittest.TestCase):
    def test_str(self):
        s = str(HalfOpenInterval(1,3))
        self.assertEqual(s, '1:3')
    
    def test_Symbols(self):
        s = str(HalfOpenInterval(Symbol('halo'), Symbol('I') - Symbol('halo')))
        self.assertEqual(s, 'halo:I-halo')

class ClosedInterval_test(unittest.TestCase):
    def test_str(self):
        s = str(ClosedInterval(1,3))
        self.assertEqual(s, '1..3')
    
    def test_Symbols(self):
        s = str(ClosedInterval(Symbol('halo'), Symbol('I') - Symbol('halo')))
        self.assertEqual(s, 'halo..I-halo')


class ToMemoryLayout_test(unittest.TestCase):
    def test_transforms_1D_to_memory_layout(self):
        original = 'i'
        for p in permutations(original):
            self.assertEqual(list(p), ToMemoryLayout(original, ''.join(p)))

    def test_transforms_2D_to_memory_layout(self):
        original = 'ij'
        for p in permutations(original):
            self.assertEqual(list(p), ToMemoryLayout(original, ''.join(p)))

    def test_transforms_3D_to_memory_layout(self):
        original = 'ijk'
        for p in permutations(original):
            self.assertEqual(list(p), ToMemoryLayout(original, ''.join(p)))

    def test_transforms_7D_to_memory_layout(self):
        original = 'abcdefg'
        for p in permutations(original):
            self.assertEqual(list(p), ToMemoryLayout(original, ''.join(p)))


class Dimensions_test(unittest.TestCase):
    def test_2D_strides(self):
        i,j,k = 5,6,7
        self.assertEqual([j,1], Dimensions([0,0,0], [i,j,k], 'ijk').ij.strides)
        self.assertEqual([j,1], Dimensions([0,0,0], [i,j,k], 'ikj').ij.strides)
        self.assertEqual([1,i], Dimensions([0,0,0], [i,j,k], 'jik').ij.strides)
        self.assertEqual([1,i], Dimensions([0,0,0], [i,j,k], 'jki').ij.strides)
        self.assertEqual([j,1], Dimensions([0,0,0], [i,j,k], 'kij').ij.strides)
        self.assertEqual([1,i], Dimensions([0,0,0], [i,j,k], 'kji').ij.strides)

    def test_3D_strides(self):
        i,j,k = 5,6,7
        self.assertEqual([j*k,k,1], Dimensions([0,0,0], [i,j,k], 'ijk').ijk.strides)
        self.assertEqual([k*j,1,j], Dimensions([0,0,0], [i,j,k], 'ikj').ijk.strides)
        self.assertEqual([k,i*k,1], Dimensions([0,0,0], [i,j,k], 'jik').ijk.strides)
        self.assertEqual([1,k*i,i], Dimensions([0,0,0], [i,j,k], 'jki').ijk.strides)
        self.assertEqual([j,1,i*j], Dimensions([0,0,0], [i,j,k], 'kij').ijk.strides)
        self.assertEqual([1,i,i*j], Dimensions([0,0,0], [i,j,k], 'kji').ijk.strides)

    def test_3D_strides(self):
        i,j,k = 5,6,7
        self.assertEqual([j*k,k,1], Dimensions([0,0,0], [i,j,k], 'ijk').ijk.strides)
        self.assertEqual([k*j,1,j], Dimensions([0,0,0], [i,j,k], 'ikj').ijk.strides)
        self.assertEqual([k,i*k,1], Dimensions([0,0,0], [i,j,k], 'jik').ijk.strides)
        self.assertEqual([1,k*i,i], Dimensions([0,0,0], [i,j,k], 'jki').ijk.strides)
        self.assertEqual([j,1,i*j], Dimensions([0,0,0], [i,j,k], 'kij').ijk.strides)
        self.assertEqual([1,i,i*j], Dimensions([0,0,0], [i,j,k], 'kji').ijk.strides)


if __name__ == '__main__':
    unittest.main()

# 3D 'ijk' -> [j*k,k,1]
# 3D 'ikj' -> [k*j,1,j]
# 3D 'jik' -> [k,i*k,1]
# 3D 'jki' -> [1,k*i,i]
# 3D 'kij' -> [j,1,i*j]
# 3D 'kji' -> [1,i,i*j]

# 2D 'ij' -> [j,1]
# 2D 'ij' -> [i,1]
# 2D 'jik' -> [k,i*k,1]
# 2D 'jki' -> [1,k*i,i]
# 2D 'kij' -> [j,1,i*j]
# 2D 'kji' -> [1,i,i*j]