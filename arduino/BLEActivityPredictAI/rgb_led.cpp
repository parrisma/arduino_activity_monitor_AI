#include "rgb_led.h"

/*
   Trivial class to encapsulate the managment of the built in LED.
*/

// Class (static) defualts
const int RgbLed::kRgbOn = LOW;
const int RgbLed::kRgbOff = HIGH;
const int RgbLed::kRed = 22;
const int RgbLed::kBlue = 24;
const int RgbLed::kGreen = 23;
const int RgbLed::kOff = 0;
const int RgbLed::kOnBoard = LED_BUILTIN;


const int RgbLed::kCycleCount = 12;
const int RgbLed::kCycleIntervalOnMillis = 100;
const int RgbLed::kCycleIntervalOffMillis = 50;

RgbLed::RgbLed() {
  // intitialize the digital Pin as an output
  pinMode(this->kRed, OUTPUT);
  pinMode(this->kBlue, OUTPUT);
  pinMode(this->kGreen, OUTPUT);

  digitalWrite(this->kRed, this->kRgbOff);
  digitalWrite(this->kGreen, this->kRgbOff);
  digitalWrite(this->kBlue, this->kRgbOff);
}

/* Set build in LED to Red colour
*/
void RgbLed::red() {
  this->off();
  this->last_colour = kRed;
  digitalWrite(this->last_colour, this->kRgbOn);
  return;
}

/* Set build in LED to Blue colour
*/
void RgbLed::blue() {
  this->off();
  this->last_colour = kBlue;
  digitalWrite(this->last_colour, this->kRgbOn);
  return;
}

/* Set build in LED to Green colour
*/
void RgbLed::green() {
  this->off();
  this->last_colour = kGreen;
  digitalWrite(this->last_colour, this->kRgbOn);
  return;
}

/* Turn the on-board LED on
*/
void RgbLed::onBoardOn() {
  digitalWrite(RgbLed::kOnBoard, HIGH);
}

/* Turn the on-board LED off
*/
void RgbLed::onBoardOff() {
  digitalWrite(RgbLed::kOnBoard, LOW);
}

/* Set build in LED to off.
*/
void RgbLed::off() {
  if (this->last_colour != this->kOff ) {
    digitalWrite(this->last_colour, this->kRgbOff);
    this->last_colour = this->kOff;
  }
  return;
}

/* Cycle all the colors
    param: cycle_times: The number of times to cycle for
    param: cycle_interval: the number of milli seconds to flash for
*/
void RgbLed::cycle(int cycle_count,
                   int cycle_interval_on,
                   int cycle_interval_off) {

  int cycle[6] = {this->kBlue,
                  this->kOff,
                  this->kRed,
                  this->kOff,
                  this->kGreen,
                  this->kOff
                 };
  const int cycle_len = sizeof(cycle) / sizeof(cycle[0]);
  int cycles = 0;
  int i = 0;

  while (cycles < cycle_count) {
    this->off();
    if (cycle[i] == this->kOff) {
      delay(cycle_interval_off);
    } else {
      switch (cycle[i]) {
        case this->kRed:
          this->red();
          break;
        case this->kGreen:
          this->green();
          break;
        case this->kBlue:
          this->blue();
          break;
        default:
          this->off();
          break;
      }
      delay(cycle_interval_on);
    }
    i++;
    if (i == cycle_len) {
      i = 0;
    }
    cycles ++;
  }
  this->off();
  return;
}
