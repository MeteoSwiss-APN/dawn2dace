import sympy
from Intermediates import Any3D

def ToMemLayout(value:Any3D) -> Any3D:
    """ Rearanges the indices to match the memory layout. """
    i, j, k = value.i, value.j, value.k    
    return Any3D(j, k, i) # Memory 
    
def FromMemLayout(value:Any3D) -> Any3D:
    for i in range(5):
        value = ToMemLayout(value)
    return value

def Pad(sizes:Any3D) -> Any3D:
    """ Pads the sizes. """
    sizes = ToMemLayout(sizes)
    sizes.k = 8 * sympy.ceiling(sizes.k / 8) # padding policy
    sizes = FromMemLayout(sizes)
    return sizes