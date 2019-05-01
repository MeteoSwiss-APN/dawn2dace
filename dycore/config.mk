GRIDTOOLS   = -DBACKEND_MC -I/<path-to-gridtools-install>/include/
GTCLANG     = -isystem <path-to-gtclang-install>/include
BOOST       = -isystem <path-to-boost>/include
DACE        = -I/<path-to-dace>/dace/runtime/include -std=c++14
COMPILER    = g++