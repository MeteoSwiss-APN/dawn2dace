import unittest
from helpers import *

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


# class RelativeNumberToStr(unittest.TestCase):
#     def test_positive(self):
#         self.assertEqual(str(RelativeNumber('A', 1)), 'A+1')

#     def test_negative(self):
#         self.assertEqual(str(RelativeNumber('A', -1)), 'A-1')

#     def test_zero(self):
#         self.assertEqual(str(RelativeNumber('A', 0)), 'A')

#     def test_add(self):
#         rn1 = RelativeNumber('A', 1)
#         rn2 = RelativeNumber('B', 2)
#         rn = rn1 + rn2
#         self.assertEqual(str(rn), 'A+B+3')

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

if __name__ == '__main__':
    unittest.main()