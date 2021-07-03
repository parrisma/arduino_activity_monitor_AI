#ifndef ACCELEROMETER_READINGS_H
#define ACCELEROMETER_READINGS_H

#include <Arduino_LSM9DS1.h>

//#define DEBUG_LG
#undef ACC_DEBUG

#ifdef ACC_DEBUG
#define DSHOW(X) X.show();
#else
#define DSHOW(X)
#endif

class AccelerometerReadings  {
  private:
    static bool imu_initialised;

    AccelerometerReadings();
    int _buffer_length;
    int _insert_point;
    float **_readings;

    bool _initialised();
    
  public:

    AccelerometerReadings(const int buffer_length);
    ~AccelerometerReadings();
    void push(const float x, const float y, const float z);
    bool initialise();
    void update_with_next_reading();
    void show();
    bool get_model_input(float * input_tensor);
};

#endif // ACCELEROMETER_READING_H
