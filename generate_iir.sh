#!/bin/bash
GTCLANG=/home/dominic/work/dawn/gtclang/bundle/install/bin/gtclang

FILES=src/{synthetic_stencils,natural_stencils}/*.cpp

for fullfile in src/*_stencils/*.cpp
do
	echo "Processing $fullfile ..."
	filename="${fullfile##*/}"
	$GTCLANG $fullfile -fwrite-iir -iir-format=byte -fdebug -fpartition-intervals -o gen/$filename
done