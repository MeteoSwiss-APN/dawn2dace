import sympy
from Intermediates import Any3D

def ToMemLayout(value:Any3D) -> Any3D:
    i, j, k = value.i, value.j, value.k
    
    return Any3D(j, k, i) # Memory layout

def ToStridePolicy3D(value:Any3D) -> Any3D:
    # Transform to memory layout
    value = ToMemLayout(value)

    # Adapt lowest order memory access
    value.k = 8 * sympy.ceiling(value.k / 8)

    # Transform back from memory layout
    value = ToMemLayout(value)
    value = ToMemLayout(value)
    value = ToMemLayout(value)
    value = ToMemLayout(value)
    value = ToMemLayout(value)

    return value