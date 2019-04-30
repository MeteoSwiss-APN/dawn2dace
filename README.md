## dawn2dace

### How to build

```
mkdir build
cd build
cmake ..
make protobuf
make 
virtualenv -p python3 my_venv
source my_venv/bin/activate
pip install --upgrade <path-to-dace>/
pip install --upgrade ./prefix/protobuf/python
```

### Using the parser:

```
export PYTHONPATH=`pwd`/gen/iir_specification
cd ../parser
python dawn2dace.py ../integration_tests/generated/1-copy_stencil.iir
```

  
