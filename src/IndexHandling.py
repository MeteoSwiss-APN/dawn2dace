
def ToMemLayout(i, j, k) -> list:
    memory_layout = [j, k, i] # Memory layout
    return [x for x in memory_layout if x is not None]

class Index3D:
    def __init__(self, i:int, j:int, k:int):
        self.i = i
        self.j = j
        self.k = k

    def MemLayouted(self) -> list:
        return ToMemLayout(self.i, self.j, self.k)