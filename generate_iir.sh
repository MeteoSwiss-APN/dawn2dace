#!/bin/bash
GTCLANG=/usr/local/dawn/bin/gtclang

cd /home/work/dawn2dace/gen

for fullfile in /home/work/dawn2dace/src/*_stencils/*.cpp
do
	echo "Processing $fullfile ..."
	filename="${fullfile##*/}"
	$GTCLANG $fullfile -write-iir -fno-codegen -iir-format=byte -o /home/work/dawn2dace/gen/$filename
done


for fullfile in /home/work/clang-gridtools/stencils/*.cpp
do
	echo "Processing $fullfile ..."
	filename="${fullfile##*/}"
	$GTCLANG $fullfile -write-iir -fno-codegen -iir-format=byte -o /home/work/dawn2dace/gen/$filename --config=/home/work/clang-gridtools/benchmarks/globals_benchmarks.json -finline
done
