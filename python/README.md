# Utilities (Python)

This is a set of Python utilities for running experiments at your desk and also to train and export the Neural network that is used by the Arduino Nano.

All the program below has a command line interface if you type <code>-h</code>

To run these programs you will need to set-up the correct python environment. You can either

* Install Anaconda and load this environment file See [full project environment](./python/conda/activity_monitor_conda_env.yml)</code>
* Or inspect the <code>[activity_monitor_conda_env.yml](./python/conda/activity_monitor_conda_env.yml)</code> file and install all the individual elements.

These environments assume a TensorFlow compatible GPU is installed as they contain the GPU version fo TensorFlow. You don't need a GPU as the model and data are small, but you may need to update the environment to the non GPU version of TensorFlow.

## <code>MainDataCollect.py</code>
This connects to the Arduino nano and collects accelerometer readings to act as training data.

The data files are stored in the <code>[data](./data)</code> folder.

It is the partner program to the Arduino program [BLEAccDataCollect](../arduino/BLEAccDataCollect)

## <code>MainFileActivityClassifier.py</code>
This program takes the collected training data and creates and trains a neural network. It is also capable of exporting the the trained neural network in the binary TensorFlow Lite form.

It is the program that generates the neural network needed by the Arduino project [BLEActivityPredictAI](../arduino/BLEActivityPredictAI). The trained Neural network is in binary form that is held as part of the program in the source file <code>[activity_model.cpp](./BLEActivityPredictAI/activity_model.cpp)</code>. Once the new Network is exported you need to overwrite both <code>activity_model.cpp</code> and <code>activity_model.h</code> in this project and re-upload to the nano.

## <code>file</code>
## <code>file</code>
## <code>file</code>
## <code>file</code>
## <code>MainConvertJson.py</code>
All three components (python/c++/DART) share the same settings as a [Json](./conf.json) file. However the Json file needs to be converted to a litter form to be added into the Arduino project. This program takes the current Json settings file and exports is as <code>json_conf.cc & json_conf.h</code>  


