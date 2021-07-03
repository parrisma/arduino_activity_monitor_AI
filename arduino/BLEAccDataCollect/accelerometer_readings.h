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

#define K_BUF_LEN 35

class AccelerometerReadings  {
  private:
    static bool imu_initialised;

    AccelerometerReadings();
    int _buffer_length;
    int _insert_point;
    char _buf[K_BUF_LEN];
    float **_readings;

    bool _initialised();
    void _push(const float x, const float y, const float z);

  public:

    static const int kBufLen;

    AccelerometerReadings(const int buffer_length);
    ~AccelerometerReadings();
    bool initialise();
    void update_with_next_reading();
    void show();
    bool get_readings_as_model_input_tensor(float * input_tensor);
    char * get_readings_as_string();
};

#endif // ACCELEROMETER_READING_H
