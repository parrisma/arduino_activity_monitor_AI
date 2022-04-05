# Arduino

Two programs for running on the Arduino Nano 33 Sense BLE.

The code is in C++ and developed in Arduino studio. Connect the Nano via UBS to the computer running Arduino studio. The Select Tools > Port and port with the Nano on it. Then upload the program. 

When the program is uploaded OK it with flash the onboard LED in a colour sequence and then steady green if anything goes wrong while the program is starting the LED will remain steady red. To find out why turn on Tools > Serial Monitor and press the little white reset button on the Nano. Now when the Nano starts it will write a text debug trace to the serial console that has been started.

## Data Collector (BLEAccDataCollect)

The program collects accelerometer readings and sends them over Bluetooth to either Python test programs as part of this wider project or to the Flutter mobile App so you can collect data on the move.

Nothing is sent until a Bluetooth connection is made at which point the on-board LED will go Blue and stay blue all the while the other end is connected. When the other end disconnects the LED will revert to stead green. 


## Activity Predictor (BLEActivityPredictAI)

The program collects accelerometer readings and then sends real time movement predictions over Bluetooth. 

The code is in C++ and developed in Arduino studio. Connect the Nano via UBS to the computer running Arduino studio. The Select Tools > Port and port with the Nano on it. Then upload the program.

When the program is uploaded OK it with flash the onboard LED in a colour sequence and then steady green if anything goes wrong while the program is starting the LED will remain steady red. To find out why turn on Tools > Serial Monitor and press the little white reset button on the Nano. Now when the Nano starts it will write a text debug trace to the serial console that has been started.

Nothing is sent until a Bluetooth connection is made. When a connection is made the program sends predictions as text strings over Bluetooth and also sets the on-board LED green, blue or red depending on which activity is being predicted  

The trained Neural network is in binary form that is held as part of the program in the source file <code>[activity_model.cpp](./BLEActivityPredictAI/activity_model.cpp)</code>. To update this model you will need to retain it using the python utility <code>[MainFileActivityClassifier.py](../python/MainFileActivityClassifier.py)</code>. This program has command line options for both training and exporting the Network. Once the new Network is exported you need to overwrite both <code>activity_model.cpp</code> and <code>activity_model.h</code> in this project and re-upload to the nano. 
