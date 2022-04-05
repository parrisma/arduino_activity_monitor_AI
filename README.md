# Activity Predictor

This project is an educational experiment to recreate the behaviour of a smart-watches ability to predict types of exercise.

To do this we use an Arduino Nano Sense 33 BLE to capture the movement and also to locally run a trained neural network to do the activity prediction.

The Project is in three parts

##Technologies & tools used

* Python 3.8
* PyCharm
* Anaconda - See <code>[full project environment](./python/conda/activity_monitor_conda_env.yml)</code>
* TensorFlow, TensorFlow Lite, Keras
* C++
* Arduino Studio
* Flutter/DART
* Android Studio
* BlueTooth (Flutter Blue and BleakScanner/BleakClient)

## 1. Utilities & Neural network training (Python)

These utilities are used to capture data, train a neural network and also export the network using TensorFlow Lite so it can be incorporated in the Arduino predictor program

Read [more](./python/README.md)

## 2. Arduino Nano Programs (C++)

There are two programs here, one for using the Nano as a training data collector over Bluetooth and one for running a trained neural network and publishing movement predictions over Bluetooth 

Read [more](./arduino/README.md)

## 3. Mobile Application (Flutter/DART)

A simple mobile application that can interact with the two Nano programs to both collect training data on the move and also make predictions on the move.

Read [more](./andriod_activity_predictor/README.md)
