#include "Arduino.h"
#include <stdlib.h>
#include <TensorFlowLite.h>
#include "accelerometer_readings.h"

/*
   Dynamically allocate the buffer to hold the accelerometer readings. This will
   match the window size required by the Neural network we are using to make the
   activity prediction with.

   We only allocate the memory once and then use pointer manipulation to shuffle down
   the contents as new items are push that cause the oldest item to be overwritten.
*/
AccelerometerReadings::AccelerometerReadings(const int buffer_length) {
  _insert_point = 0;
  _buffer_length = buffer_length;
  _readings = (float**)malloc(sizeof(int*) * _buffer_length);
  for (int i = 0 ; i != _buffer_length ; i++) {
    _readings[i] = (float*)malloc(sizeof(float) * 3); // each row is 3 readings, x,y,z
    _readings[i][0] = (float)0;
    _readings[i][1] = (float)0;
    _readings[i][2] = (float)0;
  }
}

/*
   Release all the dynamically allocated memory used by the buffer.
*/
AccelerometerReadings::~AccelerometerReadings() {
  for (int i = 0 ; i != _buffer_length ; i++) {
    free(_readings[i]);
    _readings[i] = (float*)NULL;
  }
  free(_readings);
  _readings = (float**)NULL;
}

/*
   Push the given x,y,z reading into the buffer. If the buffer is full then
   shift all the previous readings down 1 place. Drop the oldest reading and
   put the given reading in the newest slot (= slot 0)

   If the readings are full, then we shuffle down the contents so we can put the
   new reading in teh first position. We do this by copying the pointers to the
   reading arrays of x,y,z rather than copying the readings. We then put the
   readings that were in teh oldest slot in teh first slot and overwrite those
   readings with the new readings.

   This means we only do pointer manipulation to suffle down the contents and
   as we re-use the old readings to become the first readings we dont do any
   memory re-allocation either.
*/
void AccelerometerReadings::push(const float x, const float y, const float z) {
  int update_point;

  if (_insert_point == _buffer_length) {
    float * tmp = _readings[_buffer_length - 1];
    for (int i = _buffer_length - 1 ; i != 0 ; i--) {
      _readings[i] = _readings[i - 1];
    }
    update_point = 0;
    _readings[0] = tmp;
  } else {
    update_point = _insert_point;
    _insert_point++;
  }
  _readings[update_point][0] = x;
  _readings[update_point][1] = y;
  _readings[update_point][2] = z;
  return;
}

/*
   Convert the rolling window of accelerometer reading to a model input tensor.

   _buffer_length is the window size expected by the model and we always have
   three readings x,y,z. So we always write _buffer_length * 3 into the model
   input tensor that is passed. So it is essential to ensure that the _buffer_length
   is equal to the second dimension expected by the model.

   This function does not allocate memory for the input tensor which is why it
   is key to make sure the number of floats written matches the number allocated
   by the model interpreter.

   Also note that the input tensor is a flat tensor unlike in Python where the
   input tensor is dimensional. e.g. Python input tensor is e.g. float[1,20,3,1]
   and here it is float[60] = (1 * 20 * 3 * 1)

   i.e. interpreter->input(0)->data[1] == _buffer_length.

   If less then _buffer_length readings have been pushed to this collection
   then the function returns false and nothing is written to the input vector.
*/
bool AccelerometerReadings::get_model_input(float * input_tensor) {
  // Do we have a full windows worth of readings ?
  bool tensor_returned = false;
  if (_insert_point == _buffer_length) {
    for (int i = 0 ; i < _buffer_length ; i++) {
      for (int j = 0; j < 3; j++) {
        input_tensor[(i * 3) + j] = _readings[i][j];
      }
    }
    tensor_returned = true;
  }
  return tensor_returned;
}

/*
   As debug aid print the buffer contents.
*/
void AccelerometerReadings::show() {
  Serial.print("insert :");
  Serial.println(_insert_point);
  Serial.println("");
  for (int i = 0 ; i != _buffer_length ; i++) {
    Serial.print("ptr ");
    Serial.print((int)_readings[i]);
    Serial.print("x ");
    Serial.print(_readings[i][0]);
    Serial.print(" y ");
    Serial.print(_readings[i][1]);
    Serial.print(" z");
    Serial.print(_readings[i][2]);
    Serial.println("");
  }
  Serial.println("---");
  Serial.flush();
}
