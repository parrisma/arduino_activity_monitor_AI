#ifndef PREDICT_H
#define PREDICT_H

#include "debug_log.h"
#include "rgb_led.h"

class Predict  {
  private:
    const int _num_classes = 3;
    char **_class_names ;
    RgbLed _rgb_led;

    int _argmax(float *a);
  public:
    Predict();
    void initialise(RgbLed rbg_led,
                    char **class_name);
    void predict(float *prediction_tensor);
};

#endif // PREDICT_H
