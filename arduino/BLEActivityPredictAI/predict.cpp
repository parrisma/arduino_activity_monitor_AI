#include "predict.h"

Predict::Predict() {
  return;
}

void Predict::initialise(RgbLed rgb_led,
                         char **class_names) {
  this->_class_names = class_names;
  this->_rgb_led = rgb_led;
  return;
}

/*
   Return the index of the largest number.
*/
int Predict::_argmax(float *a) {
  int idx = 0;
  int mx_idx = 0;
  float mx = 1.0e-12;
  do {
    if (a[idx] > mx) {
      mx = a[idx];
      mx_idx = idx;
    }
    idx++;
  } while (idx != this->_num_classes);
  return mx_idx;
}

/*
  Take a tensor of softmax predictions. find the argmax and set the color of the RGB
  to match the prediction.
*/
void Predict::predict(float *prediction_tensor) {
  for (int i = 0; i < this->_num_classes; i++) {
    DPRINT(this->_class_names[i]);
    DPRINT(" - ");
    DPRINTLN(prediction_tensor[i]);
  }

  int prediction = this->_argmax(prediction_tensor);
  DPRINT("Prediction : ");
  switch (prediction) {
    case 0:
      this->_rgb_led.red();
      DPRINTLN(this->_class_names[prediction]);
      break;
    case 1:
      this->_rgb_led.blue();
      DPRINTLN(this->_class_names[prediction]);
      break;
    case 2:
      this->_rgb_led.green();
      DPRINTLN(this->_class_names[prediction]);
      break;
    default:
      this->_rgb_led.off();
      DPRINTLN("** ERROR **: Unknown prediction class");
      break;
  }
  return;
}
