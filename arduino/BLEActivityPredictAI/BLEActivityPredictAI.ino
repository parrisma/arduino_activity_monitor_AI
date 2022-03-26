/*
  Activity Predictor.

  For the Arduion Nano 33 BLE Sense.

  This Service samples the on board accleromiter vales every <x> milli seconds and predicts one of a defined set of
  activities / motions.

  The activity prediction is carried out by a nerual network running under Tensorflow Lite. This model is trained
  remotly on test data that is collected via a different sketch BLEAccDataCollect. The trained model is then
  converted to TF Lite format and imported here as LSTM-Activity-Model.h

  This code is extended from the magic-wand TF Lite sample from the TensorFlow folks at Google as per the Apache 2.0
  licence below.

  ==============================================================================
  /* Copyright 2019 The TensorFlow Authors. All Rights Reserved.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
  ==============================================================================

  See also" https://www.tensorflow.org/lite/microcontrollers/get_started_low_level

*/

#include "debug_log.h"

#include <TensorFlowLite.h>

#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "activity_model.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"
#include "accelerometer_readings.h"
#include "predict.h"
#include "rgb_led.h"
#include "read_conf.h"
#include "json_conf.h"
#include <Arduino_LSM9DS1.h>
#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>


/*
   Globals as variables need to be visible to both setup() and loop() Arduion callbacks
*/
namespace {

tflite::ErrorReporter* error_reporter = nullptr;
const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;
TfLiteTensor* output = nullptr;
int inference_count = 0;

/*
   Working space to TF Lite to run the model. Size varies depending on the
   specific model imported via activity_model.cpp; The size estimate can
   be done using
*/
uint8_t * tensor_arena;

/* Manage accelerometer readings.
*/
AccelerometerReadings * accelerometer_readings = NULL;
float * input_tensor = NULL;

/* Manage the on board colour LED
*/
RgbLed rgb_led;

/* Class to manage predictions based on accelerometer readings & the loaed TF (lite) model
*/
Predict predictor;

/* JSON Config reader
*/
ReadConf * config_reader = NULL;
ReadConf::BlePredictorConfig const * ble_predictor_config = NULL;
ReadConf::BleCNNConfig const * ble_cnn_config = NULL;
ReadConf::BleClassesConf const * ble_classes_config = NULL;

/* Time tracking to detect sample & predict interval expiry in loop()
*/
long previousMillis = 0;
long prevPredMillis = 0;

/* Bluetooth (Low Energy) Service & Characteristic.
*/
BLEService * ActivityPredictorService; // value set from json config

// BLE Characteristic (message) - Value set from JSON config
BLECharacteristic * PredictChar = NULL;
int ble_message_len = 0; // number of bytes to send over BLE - set from JSON config.
char * ble_message_buffer = (char *)NULL;

/* Control var to indicate when all services have started OK
*/
bool started_ok = false;

}  // namespace

/*
   =======================================================

   setpu() called once to initialise the Arduion.

   1. Bootstrap all Tensor Flow Lite Constructs
   2. Initialise the Accelerometer IMU & Acceleromoter readings.

   =======================================================
*/
void setup() {

  rgb_led.blue(); // Blue used to mean initialising

#ifdef DEBUG_LG
  Serial.setTimeout(5000);
  Serial.begin(9600);    // initialize serial communication
#endif

  /* Load thr JSON config that is exported from the host python project so that this
     sketch and the python servers share exactly teh same config.
  */
  config_reader = new ReadConf();
  if (!config_reader->begin()) { // Parse JSON config.
    DPRINTLN("Failed to parse JSON configuration.");
    return;
  }
  DPRINTLN("Jason config has been parsed OK");

  /* Extract predictor configuration.
  */
  ble_predictor_config = (ReadConf::BlePredictorConfig const *)&config_reader->get_ble_predictor_config();
  ble_cnn_config = (ReadConf::BleCNNConfig const *)&config_reader->get_ble_cnn_config();
  ble_classes_config = (ReadConf::BleClassesConf const *)&config_reader->get_ble_classes_config();

  /* Bootstrap the Bluetooth capability
  */
  DPRINT("Svc:- [");
  DPRINT(ble_predictor_config->service_name.c_str());
  DPRINTLN("]");
  ble_message_len = ble_predictor_config->characteristic_len;
  Serial.print("Characteristic Len :-");
  Serial.println(ble_message_len);
  ActivityPredictorService = new BLEService(ble_predictor_config->service_uuid.c_str());
  PredictChar = new BLECharacteristic(ble_predictor_config->characteristic_uuid_ble.c_str(), BLERead | BLENotify, ble_message_len, (1 == 1) );
  ble_message_buffer = (char *)malloc(sizeof(char) * ble_message_len); // fixed length buffer to send BLE message in via the BLE characteristic

  Serial.print("Characteristic UUID :-");
  Serial.println(PredictChar->uuid());
  if (!BLE.begin()) {
    DPRINTLN("Failed to initialize Bluetooth!");
    return;
  }
  DPRINTLN("Bluetooth started");

  /* BLE Activity Collector Service - set local name & characteristics
  */
  BLE.setLocalName(ble_predictor_config->service_name.c_str());
  BLE.setAdvertisedService(*ActivityPredictorService); // add the service UUID
  ActivityPredictorService->addCharacteristic(*PredictChar); // add prediction characteristic
  BLE.addService(*ActivityPredictorService); // Add the  service
  PredictChar->writeValue("??????????"); // set initial value, no prediction

  /* Start advertising BLE.  It will start continuously transmitting BLE
     advertising packets and will be visible to remote BLE central devices
     until it receives a new connection */

  // start advertising the Bluetooth service
  BLE.advertise();

  /* Manager for Accelerometer readings
  */
  accelerometer_readings = new AccelerometerReadings(ble_cnn_config->look_back_window_size);
  input_tensor = (float*)malloc(sizeof(float) * ble_cnn_config->look_back_window_size * ble_cnn_config->num_features);

  /*
     Set up logging. Google style is to avoid globals or statics because of
     lifetime uncertainty, but since this has a trivial destructor it's okay.
     NOLINTNEXTLINE(runtime-global-variables)
  */
  DPRINTLN("Initialise TF Lite Logging");
  static tflite::MicroErrorReporter micro_error_reporter;
  error_reporter = &micro_error_reporter;
  TF_LITE_REPORT_ERROR(error_reporter, "Error Reporter enabled.");

  /*
    Map the model into a usable data structure. This doesn't involve any
    copying or parsing, it's a very lightweight operation.
  */
  DPRINTLN("Loading tensforflow model to be ready for interence");
  model = tflite::GetModel(activity_model);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    TF_LITE_REPORT_ERROR(error_reporter,
                         "** ERROR ** : Model provided is schema version %d not equal "
                         "to supported version %d.",
                         model->version(), TFLITE_SCHEMA_VERSION);
    rgb_led.red(); // red to indicate error
    return;
  }
  TF_LITE_REPORT_ERROR(error_reporter, "Activity Model loaded.");

  /*
     This pulls in all the operation implementations we need.
     NOLINTNEXTLINE(runtime-global-variables)
  */
  DPRINTLN("Resolving the neural net operations used by the model.");
  static tflite::AllOpsResolver resolver;
  TF_LITE_REPORT_ERROR(error_reporter, "Model operations resolved");

  // Build an interpreter to run the model with.
  DPRINTLN("Starting the tensor flow micro interpreter");
  const int tensor_arena_size = (const int)ble_cnn_config->arena_size;
  tensor_arena = (uint8_t *)malloc(sizeof(uint8_t) * tensor_arena_size);
  static tflite::MicroInterpreter static_interpreter(
    model, resolver, tensor_arena, tensor_arena_size, error_reporter);
  interpreter = &static_interpreter;
  TF_LITE_REPORT_ERROR(error_reporter, "Micro Interpreter running");

  /*
    Allocate memory from the tensor_arena for the model's tensors.
  */
  DPRINTLN("Allocating model tensors");
  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    TF_LITE_REPORT_ERROR(error_reporter, "** ERROR ** : AllocateTensors() failed");
    rgb_led.red(); // red to indicate error
    return;
  }
  TF_LITE_REPORT_ERROR(error_reporter, "Tensors allocated in Arena");

  /*
    Log the model input dimensions
  */
  input = interpreter->input(0);
  DPRINT("Model input dimensions: ");
  DPRINTLN(input->dims->size);
  for (int i = 0 ; i != input->dims->size ; i++) {
    DPRINT("\t\tDim :");
    DPRINT(i);
    DPRINT(" = ");
    DPRINTLN(input->dims->data[i])  ;
  }

  DPRINTLN("Initialise Accelerometer IMU");
  if (!accelerometer_readings->initialise()) {
    DPRINTLN("** ERROR ** : Accelerometer IMU Initalisation failed !!!");
    rgb_led.red(); // red to indicate error
    return;
  }
  DPRINTLN("Accelerometer IMU OK");

  DPRINTLN("Initialse class predictor");
  predictor.initialise(rgb_led, ble_classes_config->class_names);

  rgb_led.cycle(24);
  rgb_led.green();
  started_ok = true;
}

/*
   Every <SAMPLE_INTERVAL_MILLI_SEC> take a new accelerometer reading and update the
   buffer of accelerometer readings

   Every <PREDICTION_INTERVAL> check to see if we have sufficent accelerometer readings
   and if so convert them to a form that can be passed to the TF Lite model for prediction

   Pass the model results to the prediction interpreter which will set the RGB led according
   to which of the three prediction classes is detected
*/
void loop() {
  long currentMillis = millis();
  long currPredMillis = currentMillis;

  if (started_ok) { // Did set-up finish sucessfuly.

    /* If sample interval has passed take a new accelerometer sample.
    */
    if (currentMillis - previousMillis >= ble_predictor_config->sample_interval) {
      previousMillis = currentMillis;
      accelerometer_readings->update_with_next_reading();

      /* If the prediction interval as passed check to see if we can make
         a model prediction.
      */
      if (currPredMillis - prevPredMillis >= ble_predictor_config->predict_interval) {
        BLEDevice central = BLE.central(); // wait for a BLE connection.

        if (central) {
          DPRINT("Connected to central: ");
          DPRINTLN(central.address());// print the central's BT address:
          rgb_led.onBoardOn();


          /* If wehave sufficent accelerometer readings attempt a prediction. The get_model_input
             method will convert the readings into teh correct form and load them directly into
             the model input tensor.
          */
          if (accelerometer_readings->get_readings_as_model_input_tensor(input->data.f)) {
            prevPredMillis = currPredMillis;
            DSHOW(*accelerometer_readings);

            /* Call the model with the latest window of accelerometer readings.
            */
            TfLiteStatus invoke_status = interpreter->Invoke();
            if (invoke_status != kTfLiteOk) {
              TF_LITE_REPORT_ERROR(error_reporter, "TF Lite model prediction invokation failed!\n");
              return;
            } else {
              char const * prediction = predictor.predict(interpreter->output(0)->data.f);
              if (prediction != NULL) {
                PredictChar->writeValue(str_2_buf(prediction, ble_message_buffer, ble_message_len));
              }
            }
          } else {
            DPRINTLN("Waiting for full set of readings");
          }
        }
        else {
          DPRINTLN("Waiting for Bluetooth connection.");
          rgb_led.onBoardOff();
        }
      }
    }
  } else {
    // We can never escape from here we just keep reporting failure until the Arduion is reset
    DPRINTLN("Activity Predictor - Failed to start");
    delay(1000);
  }
}

/* Copy the variable length string into the given fixed
   lenght buffer. Truncate if longer, pad with space char
   if shorter.
*/
char * str_2_buf(char const * c_str, // Null terminated
                 char * buf,
                 int buf_len) {
  for (int i = 0; i < buf_len; i++) {
    buf[i] = ' ';
  }
  int l = strlen(c_str);
  if (l > buf_len) {
    l = buf_len;
  }
  for (int i = 0; i < l; i++) {
    buf[i] = c_str[i];
  }
  return buf;
}
