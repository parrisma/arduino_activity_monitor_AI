# Mobile Application - Activity Monitor

This is a mobile app. written in Flutter. 

When the application starts it scans for all Bluetooth devices. Where it finds devices with names that match the service names as define in the project [conf.json](../python/conf.json) it will list them in the top section of the display. These devices the application can connect to and interact with.

All other Bluetooth devices are listed just for information in the lower section of the display.

Flutter will work with IOS or Android devices, however at this point it has only been tested on Android.

## Training Data Collector.
The application will connect to and interact with an Arduino nano running the in data collector mode, as defined in the [BLEAccDataCollect](../arduino/BLEAccDataCollect) project.

Once connected the application will initiate data collection from the Arduino accelerometer and store the file locally. These files can then be copied to where the [MainFileActivityClassifier.py](../python/MainFileActivityClassifier.py) python program can use them for training. To do this you must copy the files into the [data directory](../python/data) or where the python utility has been configured to look. 

## Prediction Display
The application will connect to interact with the Arduino nano running the [BLEActivityPredictAI](../arduino/BLEActivityPredictAI) program. In this mode as soon as the Nano establishes a Bluetooth it will strart interpreting the accelerometer readings and making movement predictions using the locally loaded TensorFlow Lite neural network. It will then transmit it predictions over Bluetooth which the application will display.

You can use the [MainLiveListener.py](../python/MainLiveListener.py) to test the Nano without the application. This Python script will also connect to teh Nano and just print the predictions on screen.

## Flutter FYI

A few flutter resources:

- [Lab: Write your first Flutter app](https://flutter.dev/docs/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://flutter.dev/docs/cookbook)

For help getting started with Flutter, visit

[online documentation](https://flutter.dev/docs), for tutorials,
samples, guidance on mobile development, and a full API reference.
