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

#include <Arduino_LSM9DS1.h>

long previousMillis = 0;
long prevPredMillis = 0;
#define SAMPLE_INTERVAL_MILLI_SEC 200
#define PREDICTION_INTERVAL 1000


// Globals, used for compatibility with Arduino-style sketches.
namespace {
tflite::ErrorReporter* error_reporter = nullptr;
const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;
TfLiteTensor* output = nullptr;
int inference_count = 0;

constexpr int kTensorArenaSize = 5000;
uint8_t tensor_arena[kTensorArenaSize];

constexpr int kSampleWindowSize = 20;
AccelerometerReadings accelerometer_readings(kSampleWindowSize);
float * input_tensor = (float*)malloc(sizeof(float) * kSampleWindowSize * 3);
RgbLed rgb_led;
Predict predictor;

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
  Serial.begin(9600);    // initialize serial communication
  while (!Serial);
#endif


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
    while (1); // Hang as this is a terminal failure
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
  static tflite::MicroInterpreter static_interpreter(
    model, resolver, tensor_arena, kTensorArenaSize, error_reporter);
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
    while (1); // Hang as this is a terminal failure
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
  if (!accelerometer_readings.initialise()) {
    DPRINTLN("** ERROR ** : Accelerometer IMU Initalisation failed !!!");
    rgb_led.red(); // red to indicate error
    while (1); // Hang as this is a terminal failure
  }
  DPRINTLN("Accelerometer IMU OK");

  DPRINTLN("Initialse class predictor");
  char ** class_names = (char **)malloc(sizeof(int) * 3);
  class_names[0] = "Circle";
  class_names[1] = "Static";
  class_names[2] = "Up/Down";
  predictor.initialise(rgb_led, class_names);

  rgb_led.cycle(24);
  rgb_led.green();
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

  /* If sample interval has passed take a new accelerometer sample.
  */
  if (currentMillis - previousMillis >= SAMPLE_INTERVAL_MILLI_SEC) {
    previousMillis = currentMillis;
    accelerometer_readings.update_with_next_reading();

    /* If the prediction interval as passed check to see if we can make
       a model prediction.
    */
    if (currPredMillis - prevPredMillis >= PREDICTION_INTERVAL) {

      /* If wehave sufficent accelerometer readings attempt a prediction. The get_model_input
         method will convert the readings into teh correct form and load them directly into
         the model input tensor.
      */
      if (accelerometer_readings.get_readings_as_model_input_tensor(input->data.f)) {
        prevPredMillis = currPredMillis;
        DSHOW(accelerometer_readings);

        /* Call the model with the latest window of accelerometer readings.
        */
        TfLiteStatus invoke_status = interpreter->Invoke();
        if (invoke_status != kTfLiteOk) {
          TF_LITE_REPORT_ERROR(error_reporter, "Invoke failed on index\n");
          return;
        } else {
          predictor.predict(interpreter->output(0)->data.f);
        }
      } else {
        DPRINTLN("Waiting for full set of readings");
      }
    }
  }
}
