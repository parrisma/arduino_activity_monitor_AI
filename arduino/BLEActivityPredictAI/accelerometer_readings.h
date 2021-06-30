#ifndef ACCELEROMETER_READINGS_H
#define ACCELEROMETER_READINGS_H

class AccelerometerReadings  {
  private:
    AccelerometerReadings();
    int _buffer_length;
    int _insert_point;
    float **_readings;
  public:

    AccelerometerReadings(const int buffer_length);
    ~AccelerometerReadings();
    void push(const float x, const float y, const float z);
};

#endif // ACCELEROMETER_READING_H
