import unittest
from IndexHandling import *

class MemoryLayout(unittest.TestCase):
    def test_inversion(self):
        a = Any3D(1,2,3)
        b = FromMemLayout(ToMemLayout(a))
        self.assertEqual(a, b)

if __name__ == '__main__':
    unittest.main()