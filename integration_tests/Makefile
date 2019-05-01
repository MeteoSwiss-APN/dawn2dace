include config.mk

all: copy_stencil inout offsets vertical_spec local_variable local_internal vertical_offsets

copy_stencil: copy_stencil_benchmark.cpp generated/copy_stencil_dace_gen.cpp generated/copy_stencil_gtclang_gen.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DAPP) copy_stencil_benchmark.cpp -o bin/copy_stencil 

inout: inout_benchmark.cpp generated/inout_dace_gen.cpp generated/inout_gtclang_gen.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DAPP) inout_benchmark.cpp -o bin/inout_stencil

offsets: offsets_benchmark.cpp generated/offsets_dace_gen.cpp generated/offsets_gtclang_gen.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DAPP) offsets_benchmark.cpp -o bin/offsets_stencil	

vertical_spec: vertical_spec_benchmark.cpp generated/vertical_spec_dace_gen.cpp generated/vertical_spec_gtclang_gen.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DAPP) vertical_spec_benchmark.cpp -o bin/vertical_specialization_stencil

local_variable: local_variable_benchmark.cpp generated/local_variable_dace_gen.cpp generated/local_variable_gtclang_gen.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DAPP) local_variable_benchmark.cpp -o bin/local_variable_stencil

local_internal: local_internal_benchmark.cpp generated/local_internal_dace_gen.cpp generated/local_internal_gtclang_gen.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DAPP) local_internal_benchmark.cpp -o bin/local_internal_stencil

vertical_offsets: vertical-offsets_benchmark.cpp generated/vertical-offsets_dace_gen.cpp generated/vertical-offsets_gtclang_gen.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DAPP) vertical-offsets_benchmark.cpp -o bin/vertical_offsets_stencil

brackets: brackets_benchmark.cpp generated/brackets_dace_gen.cpp generated/brackets_gtclang_gen.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DAPP) brackets_benchmark.cpp -o bin/brackets_stencil
run:
	./bin/copy_stencil 20 20 10
	./bin/inout_stencil 20 20 10
	./bin/offsets_stencil 20 20 10
	./bin/vertical_specialization_stencil 20 20 10
	./bin/local_variable_stencil 20 20 10
	./bin/local_internal_stencil 20 20 10
	./bin/vertical_offsets_stencil 20 20 10

clean:
	rm -rf bin/*