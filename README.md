# Activity Predictor

This project is an educational experiment to recreate the behaviour of a smart-watches ability to predict types of exercise.

To do this we use an Arduino Nano Sense 33 BLE to capture the movement and also to locally run a trained neural network to do the activity prediction.

The Project is in three parts

## 1. Utilities & Neural network training (Python)

These utilities are used to capture data, train a neural network and also export the network using TensorFlow Lite so it can be incorporated in the Arduino predictor program

Read [more](./python/README)

## 2. Arduino Nano Programs (c++)

## 3. Mobile Application (Flutter/DART)