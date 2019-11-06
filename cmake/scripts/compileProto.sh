#!/bin/bash

proto_binary=$1
source_dir=$2
binary_dir=$3 

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${binary_dir}/prefix/protobuf/lib/
mkdir -p ${binary_dir}/gen
${proto_binary} --python_out=${binary_dir}/gen ${source_dir}/iir_specification/IIR.proto -I=${source_dir} -I=${source_dir}/iir_specification/ > /tmp/log
${proto_binary} --python_out=${binary_dir}/gen ${source_dir}/iir_specification/SIR/statements.proto -I=${source_dir} > /tmp/log

