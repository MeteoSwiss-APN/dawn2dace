from sweep import *
import reference
import numpy as np

def CreateData(data_config):
    # create and save the input data
    input_data = reference.CreateInputData(*data_config)
    for index, var in enumerate(input_data):
        file_name = 'autotuning/' + InVarName(data_config, index)
        np.save(file_name, var)

    # create and save the reference output data
    output_data = reference.HD_smag(*data_config, *input_data)
    for index, var in enumerate(output_data):
        file_name = 'autotuning/' + OutVarName(data_config, index)
        np.save(file_name, var)


def main():
    sweep = CreateSweep()
    data_set = CreateDataSet(sweep)
    
    for data_config in data_set:
        CreateData(data_config)

if __name__ == "__main__":
    main()