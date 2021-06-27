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

#include <TensorFlowLite.h>

#include "main_functions.h"

#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "constants.h"
#include "model.h"
#include "activity_model.h"
#include "output_handler.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

long previousMillis = 0;
#define INTERVAL_MILLI_SEC 5000

/* RGB LED Values */
#define RED 22
#define BLUE 23
#define GREEN 24
#define LED_OFF 0

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
}  // namespace

// The name of this function is important for Arduino compatibility.
void setup() {

  // intitialize the digital Pin as an output
  pinMode(RED, OUTPUT);
  pinMode(BLUE, OUTPUT);
  pinMode(GREEN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT); // initialize the built-in LED pin to indicate when a central is 

  rgb_led(BLUE);
  
  Serial.begin(9600);    // initialize serial communication
  while (!Serial);

  Serial.println("Step 1");
  
  // Set up logging. Google style is to avoid globals or statics because of
  // lifetime uncertainty, but since this has a trivial destructor it's okay.
  // NOLINTNEXTLINE(runtime-global-variables)
  static tflite::MicroErrorReporter micro_error_reporter;
  error_reporter = &micro_error_reporter;
  TF_LITE_REPORT_ERROR(error_reporter, "Error Reporter enabled.");Serial.flush();
  
  rgb_led(RED);
  
  // Map the model into a usable data structure. This doesn't involve any
  // copying or parsing, it's a very lightweight operation.
  model = tflite::GetModel(activity_model);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    TF_LITE_REPORT_ERROR(error_reporter,
                         "Model provided is schema version %d not equal "
                         "to supported version %d.",
                         model->version(), TFLITE_SCHEMA_VERSION);
    return;
  }
  Serial.println("Step 2");
  rgb_led(BLUE);  

  TF_LITE_REPORT_ERROR(error_reporter, "Activity Model loaded.");Serial.flush();

  // This pulls in all the operation implementations we need.
  // NOLINTNEXTLINE(runtime-global-variables)
  static tflite::AllOpsResolver resolver;
  TF_LITE_REPORT_ERROR(error_reporter, "Model operations resolved");Serial.flush();

  Serial.println("Step 4");
  rgb_led(GREEN);

  // Build an interpreter to run the model with.
  static tflite::MicroInterpreter static_interpreter(
      model, resolver, tensor_arena, kTensorArenaSize, error_reporter);
  interpreter = &static_interpreter;
  TF_LITE_REPORT_ERROR(error_reporter, "Micro Interpreter running");Serial.flush();

  Serial.println("Step 5");
  rgb_led(RED);

  // Allocate memory from the tensor_arena for the model's tensors.
  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    TF_LITE_REPORT_ERROR(error_reporter, "AllocateTensors() failed @ 20000");
    return;
  }
  TF_LITE_REPORT_ERROR(error_reporter, "Tensors allocated in Arena");Serial.flush();
  Serial.println("Step 6");
}

// The name of this function is important for Arduino compatibility.
void loop() {
    long currentMillis = millis();
    // if define ms have passed, re-send lates acceleromiter values:
    if (currentMillis - previousMillis >= INTERVAL_MILLI_SEC) {
      previousMillis = currentMillis;
      Serial.println("Tick .");
    }
}

void rgb_led(int value)
{
  digitalWrite(RED, LOW);
  digitalWrite(GREEN, LOW);
  digitalWrite(BLUE, LOW);
  switch (value) {
    case RED:
      digitalWrite(RED, HIGH);
      break;
    case GREEN:
      digitalWrite(GREEN, HIGH);
      break;
    case BLUE:
      digitalWrite(BLUE, HIGH);
      break;
    case LED_OFF:
    default:
      break;
  }
}
