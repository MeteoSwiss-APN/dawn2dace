#!/bin/bash
# set -e

BASEPATH_SCRIPT=$(dirname "${0}")
SCRIPT=`basename $0`
PARSER_DIR=${BASEPATH_SCRIPT}/../../parser

function help {
  echo -e "Basic usage:$SCRIPT "\\n
  echo -e "The following switches are recognized. $OFF "
  echo -e "-g sets the gtclang executable directory"
  echo -e "-h Shows this help"
  exit 1
}

# Get the options passed
while getopts g: flag; do
  case $flag in
    g)
      GTCLANG_DIR=$OPTARG
      ;;
    h)
      help
      ;;
    \?) #unrecognized option - show help
      echo -e \\n"Option -${BOLD}$OPTARG${OFF} not allowed."
      help
      ;;
  esac
done

# check if the gtclang directory is set properly
GTCLANG_EXEC=$GTCLANG_DIR/gtclang
if $GTCLANG_EXEC --version ; then
    echo "GTClang found"
else
    echo "GTClang directory is not set correct"
    echo "found directory \`$GTCLANG_DIR\`"
    echo "aborting"
    exit 1
fi

# set the python-path to include the generated iir protobuf files
pushd ${BASEPATH_SCRIPT}/../../build/gen/iir_specification
GENERATED_PATH=`pwd`
popd
export PYTHONPATH=$GENERATED_PATH

# setup the test directory source
pushd ${BASEPATH_SCRIPT}/../../integration_tests/source/
SOURCE_DIR=`pwd`
popd

pushd $PARSER_DIR
source ../build/my_venv/bin/activate
FILES=${SOURCE_DIR}/*.cpp

#remove old generated code
rm -rf ../integration_tests/generated/*
rm -rf ../integration_tests/bin/*

# generate things for each file
for ex in $FILES ; do
    FILE_NAME="$(basename -- $ex)"
    STRIPPED_NAME="${FILE_NAME%%.*}"
    # create the iir and the gtclang generated code
    $GTCLANG_EXEC $ex -fwrite-iir -iir-format=byte -fpartition-intervals -o $STRIPPED_NAME.cpp
    mv $STRIPPED_NAME.cpp ${STRIPPED_NAME}_gtclang.cpp
    mv $STRIPPED_NAME.0.iir ${STRIPPED_NAME}.iir

    # create the SDFG and the dace-generated code
    rm -rf .dacecache/*
    python dawn2dace.py $STRIPPED_NAME.iir
    mv .dacecache/IIRToSDFG/src/cpu/IIRToSDFG.cpp ${STRIPPED_NAME}_dace.cpp
    mv after.sdfg ${STRIPPED_NAME}.sdfg
    rm before.sdfg

    # move it into the generated folder
    mkdir -p ../integration_tests/generated/
    mv ${STRIPPED_NAME}_gtclang.cpp ../integration_tests/generated/
    mv ${STRIPPED_NAME}_dace.cpp ../integration_tests/generated/
    mv ${STRIPPED_NAME}.iir ../integration_tests/generated/
    mv ${STRIPPED_NAME}.sdfg ../integration_tests/generated/
done
popd

#change to the test directory
pushd ${BASEPATH_SCRIPT}/../../integration_tests/
#build the tests
make
# run the executables
for binary in bin/*_stencil ; do
    $binary 256 256 30 || exit 1
done
popd