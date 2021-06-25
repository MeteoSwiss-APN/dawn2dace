import run
from sweep import *

def main():
    # sweep = CreateSweep()
    sweep = [
        ((128,128,80),'kij','kij',1,1,1),
        # ((256,256,80),'kij','kij',8,32,1),
        # ((512,512,80),'kij','kij',8,32,1),
        # ((1158,774,80),'kij','kij',8,32,1),
        # ((582,390,60),'kij','kij',8,32,1),
        # ((393,338,60),'kij','kij',8,32,1)
    ]
    program_set = CreateProgramSet(sweep)

    # run all
    for program_config in program_set:
        sdfg = run.CreateProgam(program_config)
        for s in sweep:
            if ProgramRelevant(s) == program_config:
                run.run(sdfg, s)

if __name__ == "__main__":
    main()