/*
  Activity Predictor.

  For teh Arduion Nano 33 BLE Sense.

  This Service samples the on board accleromiter vales every <x> milli seconds and notifies the latest x,y,z values
  via a single charactertistic. The values are updated while there is at least one connected party.
  
  This characteristic is formed as a string with the three float values aepated by a ; char. So the other end must split
  and cast back to float to get the numeric values.

  The intent of this service is to generate accleromiter training data that can be used to train a Neural network that 
  can classify the activty (walking, running, cycling) of the person holding the Nano SBC.

  The model is trained remotly and then run via tensor flow lite by a different Sketch.
*/

#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>

/* RGB LED Values */
#define RED 22
#define BLUE 23
#define GREEN 24
#define LED_OFF 0

#define BLE_SERVICE_UUID "FF01" // arbitary 
#define BLE_ACCEL_CHARACTERISTIC_UUID "F001" // arbitary

#define INTERVAL_MILLI_SEC 200

// Activity Predictor Service
BLEService ActivityPredictorService(BLE_SERVICE_UUID);

// Characteristic to transmit (stream) acceleromiter values
#define BUF_LEN 35
BLECharacteristic AccelXYZChar(BLE_ACCEL_CHARACTERISTIC_UUID, BLERead | BLENotify, BUF_LEN, (1 == 1) );

long previousMillis = 0;

/*
  Set-up the service
*/
void setup() {
  // intitialize the digital Pin as an output
  pinMode(RED, OUTPUT);
  pinMode(BLUE, OUTPUT);
  pinMode(GREEN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT); // initialize the built-in LED pin to indicate when a central is connected

  rgb_led(LED_OFF);

  Serial.begin(9600);    // initialize serial communication
  while (!Serial);

  rgb_led(RED); // Set led Red (failed/setting up) until all services are ok.
  if (!BLE.begin()) { // Low Energy Blue Tooth
    Serial.println("Failed to initialize BLE!");
    while (1);
  }
  if (!IMU.begin()) { // Acceleromitor
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  /* Activity Predictor Service - set local name & characteristics
  */
  BLE.setLocalName("ActivityPredictor");
  BLE.setAdvertisedService(ActivityPredictorService); // add the service UUID
  ActivityPredictorService.addCharacteristic(AccelXYZChar); // add X,Y,Z Acceleromiter characteristic
  BLE.addService(ActivityPredictorService); // Add the  service
  AccelXYZChar.writeValue("0.0;0,0;0.0"); // set initial value

  /* Start advertising BLE.  It will start continuously transmitting BLE
     advertising packets and will be visible to remote BLE central devices
     until it receives a new connection */

  // start advertising
  BLE.advertise();
  rgb_led(GREEN); // Led green as we are noew ready to accept connections.

  Serial.println("Activity Predictor Service, Bluetooth active, waiting for connections...");
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
      // if define ms have passed, re-send lates acceleromiter values:
      if (currentMillis - previousMillis >= INTERVAL_MILLI_SEC) {
        previousMillis = currentMillis;
        updateAcceleromiterLevels();
      }
    }
    // when the central disconnects, turn off the LED:
    rgb_led(GREEN);
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}

void updateAcceleromiterLevels() {
  /*
    Sample and notify any connected entities of the latest acceleromiter levels.
  */
  float x, y, z;
  IMU.readAcceleration(x, y, z);
  char buf[BUF_LEN];
  sprintf(buf, "%f;%f;%f\n", x, y, z);
  int lenb = strlen(buf);
  for (int i = lenb - 1; i < BUF_LEN; i++) {
    buf[i] = ' ';
  }
  Serial.println(buf);
  AccelXYZChar.writeValue(buf);
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
