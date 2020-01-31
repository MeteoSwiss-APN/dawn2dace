#!/bin/bash
GTCLANG=/home/dominic/work/dawn/build/install/bin/gtclang

cd gen

for fullfile in ../src/*_stencils/*.cpp
do
	echo "Processing $fullfile ..."
	filename="${fullfile##*/}"
	$GTCLANG $fullfile -fwrite-iir -iir-format=byte -fdebug -fpartition-intervals -o $filename
	rm $filename
done


for fullfile in ../../clang-gridtools/stencils/*.cpp
do
	echo "Processing $fullfile ..."
	filename="${fullfile##*/}"
	$GTCLANG $fullfile -fwrite-iir -iir-format=byte -fdebug -fpartition-intervals -o $filename --config=/home/dominic/work/clang-gridtools/benchmarks/globals_benchmarks.json -inline
	rm $filename
done

cd ..