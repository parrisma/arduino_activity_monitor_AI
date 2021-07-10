#ifndef RGB_LED_H
#define RGB_LED_H

#include "Arduino.h"

class RgbLed  {
  private:
    static const int kRgbOn;
    static const int kRgbOff;
    static const int kRed;
    static const int kBlue;
    static const int kGreen;
    static const int kOff;
    static const int kOnBoard;

    int last_colour;

  protected:
    /* Cycle method defaults.
    */
    static const int kCycleCount;
    static const int kCycleIntervalOnMillis;
    static const int kCycleIntervalOffMillis;

  public:
    RgbLed();
    void red();
    void blue();
    void green();
    void off();
    void onBoardOn();
    void onBoardOff();
    void cycle(int cycle_count = RgbLed::kCycleCount,
               int cycle_interval_on = RgbLed::kCycleIntervalOnMillis,
               int cycle_interval_ff = RgbLed::kCycleIntervalOffMillis);
};

#endif // RGB_LED_H
