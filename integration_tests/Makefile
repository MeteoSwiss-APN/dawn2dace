include config.mk

#all: bin/copy_stencil bin/inout_stencil bin/offsets_stencil bin/vertical_specialization_stencil bin/vertical_offsets_stencil bin/local_variable_stencil bin/local_internal_stencil bin/brackets_stencil

all: bin/copy_stencil_dace

bin/copy_stencil_dace: copy_stencil_benchmark.cpp generated/1-copy_stencil_gtclang.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) copy_stencil_benchmark.cpp -o bin/copy_stencil_dace -Wl,-rpath=../parser/.dacecache/IIRToSDFG/build -L../parser/.dacecache/IIRToSDFG/build -lIIRToSDFG -fPIC

bin/copy_stencil: copy_stencil_benchmark.cpp generated/1-copy_stencil_dace.cpp generated/1-copy_stencil_gtclang.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) copy_stencil_benchmark.cpp -o bin/copy_stencil 

bin/inout_stencil: inout_benchmark.cpp generated/2-inout_variable_dace.cpp generated/2-inout_variable_gtclang.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) inout_benchmark.cpp -o bin/inout_stencil

bin/offsets_stencil: offsets_benchmark.cpp generated/3-offsets_dace.cpp generated/3-offsets_gtclang.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) offsets_benchmark.cpp -o bin/offsets_stencil	

bin/vertical_specialization_stencil: vertical_spec_benchmark.cpp generated/4-vertical_spec_dace.cpp generated/4-vertical_spec_gtclang.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) vertical_spec_benchmark.cpp -o bin/vertical_specialization_stencil

bin/vertical_offsets_stencil: vertical-offsets_benchmark.cpp generated/5-vertical-offsets_gtclang.cpp generated/5-vertical-offsets_dace.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) vertical-offsets_benchmark.cpp -o bin/vertical_offsets_stencil

bin/local_variable_stencil: local_variable_benchmark.cpp generated/6-local-variables_dace.cpp generated/6-local-variables_gtclang.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) local_variable_benchmark.cpp -o bin/local_variable_stencil

bin/local_internal_stencil: local_internal_benchmark.cpp generated/7-local-internal_dace.cpp generated/7-local-internal_gtclang.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) local_internal_benchmark.cpp -o bin/local_internal_stencil

bin/brackets_stencil: brackets_benchmark.cpp generated/8-brackets_gtclang.cpp generated/8-brackets_dace.cpp
	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) brackets_benchmark.cpp -o bin/brackets_stencil

# fwd: forward_stencil_benchmark.cpp generated/9-forward_stencil_dace_gen.cpp generated/9-forward_stencil_gtclang_gen.cpp
# 	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) forward_stencil_benchmark.cpp -o bin/forward_stencil

# globals: global_benchmark.cpp generated/10-global-stencil_dace_gen.cpp generated/10-global-stencil_gtclang_gen.cpp
# 	$(COMPILER) $(GRIDTOOLS) $(GTCLANG) $(BOOST) $(DACE) global_benchmark.cpp -o bin/global_stencil

run:
	./bin/copy_stencil 20 20 10
	./bin/inout_stencil 20 20 10
	./bin/offsets_stencil 20 20 10
	./bin/vertical_specialization_stencil 20 20 10
	./bin/local_variable_stencil 20 20 10
	./bin/local_internal_stencil 20 20 10
	./bin/vertical_offsets_stencil 20 20 10
	./bin/brackets_stencil 20 20 10
	# ./bin/forward_stencil 20 20 10
	# ./bin/global_stencil 20 20 10

clean:
	rm -rf bin/*
