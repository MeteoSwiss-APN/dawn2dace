import unittest
from helpers import *

class Pairwise(unittest.TestCase):
    def test_list_of_0(self):
        a = list(pairwise([]))
        b = []
        self.assertEqual(a, b)

    def test_list_of_1(self):
        a = list(pairwise([1]))
        b = []
        self.assertEqual(a, b)

    def test_list_of_2(self):
        a = list(pairwise([1,2]))
        b = [(1,2)]
        self.assertEqual(a, b)
    
    def test_list_of_3(self):
        a = list(pairwise([1,2,3]))
        b = [(1,2), (2,3)]
        self.assertEqual(a, b)


class RelativeNumberToStr(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(str(RelativeNumber('A', 1)), 'A+1')

    def test_negative(self):
        self.assertEqual(str(RelativeNumber('A', -1)), 'A-1')

    def test_zero(self):
        self.assertEqual(str(RelativeNumber('A', 0)), 'A')


class Bool3D_test(unittest.TestCase):
    def test_or(self):
        a = Bool3D.Or([Bool3D(True,False,False), Bool3D(False,True,False)])
        b = Bool3D(True,True,False)
        self.assertEqual(a, b)

class HalfOpenInterval_test(unittest.TestCase):
    def test_str(self):
        a = str(HalfOpenInterval(1,3))
        b = '1:3'
        self.assertEqual(a,b)

if __name__ == '__main__':
    unittest.main()