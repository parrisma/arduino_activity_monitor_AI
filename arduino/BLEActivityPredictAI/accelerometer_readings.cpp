#include <stdlib.h>
#include "accelerometer_readings.h"

/*
   Dynamically allocate the buffer to hold the accelerometer readings. This will
   match the window size required by the Neural network we are using to make the
   activity prediction with.
*/
AccelerometerReadings::AccelerometerReadings(const int buffer_length) {
  _insert_point = 0;
  _buffer_length = buffer_length;
  _readings = (float**)malloc(sizeof(int*) * _buffer_length);
  for (int i = 0 ; i != _buffer_length ; i++) {
    _readings[i] = (float*)malloc(sizeof(float) * 3); // each row is 3 readings, x,y,z
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
*/
void AccelerometerReadings::push(const float x, const float y, const float z) {
  int update_point = 0;
  if (_insert_point == _buffer_length) {
    float * tmp = _readings[_buffer_length];
    for (int i = _buffer_length ; i != 1 ; i--) {
      _readings[i] = _readings[i - 1];
    }
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
