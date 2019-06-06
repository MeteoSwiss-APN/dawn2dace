include config.mk

all: coriolis

coriolis: coriolis_benchmark.cpp gen/coriolis_gtclang_gen.cpp gen/coriolis_dace_gen.cpp utils/benchmark_writer.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DAPP) coriolis_benchmark.cpp utils/benchmark_writer.cpp -o coriolis_stencil 
run:
	./coriolis_stencil 129 129 80

clean:
	rm -rf *_stencil