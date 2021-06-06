/*
  Activity Predictor.
*/

#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>

/* RGB LED Values */
#define RED 22
#define BLUE 23
#define GREEN 24
#define LED_OFF 0

// BLE Battery Service
BLEService batteryService("180F");

// BLE Battery Level Characteristic
BLEFloatCharacteristic AccelXChar("f001", BLERead | BLENotify); // Acceleromiter X characteristic
BLEFloatCharacteristic AccelYChar("f002", BLERead | BLENotify); // Acceleromiter y characteristic
BLEFloatCharacteristic AccelZChar("f003", BLERead | BLENotify); // Acceleromiter z characteristic

long previousMillis = 0;

void setup() {
  // intitialize the digital Pin as an output
  pinMode(RED, OUTPUT);
  pinMode(BLUE, OUTPUT);
  pinMode(GREEN, OUTPUT);
  rgb_led(LED_OFF);

  Serial.begin(9600);    // initialize serial communication
  while (!Serial);

  pinMode(LED_BUILTIN, OUTPUT); // initialize the built-in LED pin to indicate when a central is connected

  // begin initialization
  rgb_led(RED);
  if (!BLE.begin()) {
    Serial.println("Failed to initialize BLE!");
    while (1);
  }
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
  rgb_led(GREEN);

  /* Set a local name for the BLE device
     This name will appear in advertising packets
     and can be used by remote devices to identify this BLE device
     The name can be changed but maybe be truncated based on space left in advertisement packet
  */
  BLE.setLocalName("ActivityPredictor");
  BLE.setAdvertisedService(batteryService); // add the service UUID
  batteryService.addCharacteristic(AccelXChar); // add X Acceleromiter characteristic
  batteryService.addCharacteristic(AccelYChar); // add Y Acceleromiter characteristic
  batteryService.addCharacteristic(AccelZChar); // add Z Acceleromiter characteristic
  BLE.addService(batteryService); // Add the battery service
  AccelXChar.writeValue(0.0); // set initial value for this characteristic
  AccelYChar.writeValue(0.0); // set initial value for this characteristic
  AccelZChar.writeValue(0.0); // set initial value for this characteristic

  /* Start advertising BLE.  It will start continuously transmitting BLE
     advertising packets and will be visible to remote BLE central devices
     until it receives a new connection */

  // start advertising
  BLE.advertise();

  Serial.println("Bluetooth device active, waiting for connections...");
}

void loop() {
  // wait for a BLE central
  BLEDevice central = BLE.central();

  // if a central is connected to the peripheral:
  if (central) {
    Serial.print("Connected to central: ");
    // print the central's BT address:
    Serial.println(central.address());
    // turn on the LED to indicate the connection:
    rgb_led(BLUE);

    // check the battery level every 200ms
    // while the central is connected:
    while (central.connected()) {
      long currentMillis = millis();
      // if 200ms have passed, check the battery level:
      if (currentMillis - previousMillis >= 200) {
        previousMillis = currentMillis;
        updateBatteryLevel();
      }
    }
    // when the central disconnects, turn off the LED:
    rgb_led(GREEN);
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}

void updateBatteryLevel() {
  /* Write a random number ot teh characteristic
  */
  float x, y, z;
  IMU.readAcceleration(x, y, z);
  Serial.print(x, 3);
  Serial.print('\t');
  Serial.print(y, 3);
  Serial.print('\t');
  Serial.println(z, 3);
  char buf[100];
  sprintf(buf, "%f; %f; %f", x,y,z);
  Serial.println(buf);
  
  AccelXChar.writeValue(x);
  AccelYChar.writeValue(y);
  AccelZChar.writeValue(z);
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
