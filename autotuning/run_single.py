import run
from sweep import *

def main():
    s = [((128,128,80),'kij','kij',8,64,1)]

    sdfg = run.CreateProgam(ProgramRelevant(s))
    run.run(sdfg, s)

if __name__ == "__main__":
    sweep = CreateSweep()
    program_set = CreateProgramSet(sweep)