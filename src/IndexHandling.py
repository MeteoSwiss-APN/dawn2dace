
def ToMemLayout(i, j, k):
    return j, k, i # Memory layout

class Index3D:
    def __init__(self, i:int, j:int, k:int):
        self.i = i
        self.j = j
        self.k = k
