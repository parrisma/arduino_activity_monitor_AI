/*
  Activity Collector.

  For the Arduino Nano 33 BLE Sense.

  This Service samples the on board accelerometer vales every <x> milli seconds and the sends them over Bluetooth 
  via a single characteristic. The values are updated while there is at least one remote connected party.

  This characteristic is formed as a string with the three float values separated by a ; char. So the other end must split
  and cast back to float to get the numeric values.

  The intent of this service is to generate accelerometer training data that can be used to train a Neural network that
  can classify the activity (walking, running, cycling) of the person holding the Nano SBC.

  The model is trained remotely and then run via tensor flow lite by a different Sketch.
*/

#include "debug_log.h"
#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>
#include "accelerometer_readings.h"
#include "rgb_led.h"
#include "read_conf.h"
#include "json_conf.h"

// Activity Collector Service - value set from json config
BLEService * ActivityCollectorService;

// BLE Characteristic (message) - Value set from JSON config
BLECharacteristic * AccelXYZChar = NULL;
int ble_message_len = 0; // number of bytes to send over BLE - set from JSON config.

/* Global for Accelerometer and publish cycle.
*/
AccelerometerReadings * accelerometer_readings;
long previousMillis = 0;
int sample_interval = 0; // Value set from JSON config.

/* JSON Config reader
*/
ReadConf config_reader;

/* RGB Util.
*/
RgbLed rgb_led;

/* Control var to indicate when all services have started OK
*/
bool started_ok = false;

/*
  ===========================================================================================

  1. Set LED Red to indicate in failed state until all setup is passed
  2. Read JSON config so we can sync with Host Python service on shared config & BLE details.
  3. Boot-strap Bluetooth
  4. Boot-strap Accelerometer (we only use partial capability of this class here)
  5. Flash the colour LEDs then set LED to green to indicate all OK.

  ===========================================================================================
*/
void setup() {

  rgb_led.red();

#ifdef DEBUG_LG
  Serial.begin(9600);    // initialize serial communication
  while (!Serial);
#endif

  /* Load thr JSON config that is exported from the host python project so that this
     sketch and the python servers share exactly teh same config.
  */
  if (!config_reader.begin()) { // Parse JSON config.
    DPRINTLN("Failed to parse JSON configuration.");
    return;
  }
  DPRINTLN("Jason config has been parsed OK");

  ReadConf::BleConnectorConfig ble_connector_config = config_reader.get_ble_connector_config();
  sample_interval = ble_connector_config.sample_interval;
  ble_message_len = ble_connector_config.characteristic_len;

  /* Bootstrap the Bluetooth capability
  */
  DPRINT("Svc:- [");
  DPRINT(ble_connector_config.service_name.c_str());
  DPRINTLN("]");
  ActivityCollectorService = new BLEService(ble_connector_config.service_uuid.c_str());
  AccelXYZChar = new BLECharacteristic(ble_connector_config.characteristic_uuid_ble.c_str(), BLERead | BLENotify, ble_message_len, (1 == 1) );
  
  Serial.print("Characteristic UUID :-");
  Serial.println(AccelXYZChar->uuid());
  if (!BLE.begin()) {
    DPRINTLN("Failed to initialize BLE!");
    return;
  }
  DPRINTLN("Bluetooth started");

  /* BLE Activity Collector Service - set local name & characteristics
  */
  BLE.setLocalName(ble_connector_config.service_name.c_str());
  BLE.setAdvertisedService(*ActivityCollectorService); // add the service UUID
  ActivityCollectorService->addCharacteristic(*AccelXYZChar); // add X,Y,Z Acceleromiter characteristic
  BLE.addService(*ActivityCollectorService); // Add the  service
  AccelXYZChar->writeValue("0.0;0,0;0.0"); // set initial value

  /* Start advertising BLE.  It will start continuously transmitting BLE
     advertising packets and will be visible to remote BLE central devices
     until it receives a new connection */

  // start advertising the Bluetooth service
  BLE.advertise();

  /* Set-up the accelerometer
  */
  DPRINTLN("Initialise Accelerometer IMU");
  accelerometer_readings = new AccelerometerReadings(1);
  if (!accelerometer_readings->initialise()) {
    DPRINTLN("** ERROR ** : Accelerometer IMU Initialisation failed !!!");
    return;
  }
  DPRINTLN("Accelerometer IMU initialised OK");

  /* Signal all OK by sparkling the RGB lights
  */
  rgb_led.cycle();
  rgb_led.green(); // Led green as we are now ready to accept connections.
  started_ok = true;
  DPRINT(ble_connector_config.service_name.c_str());
  DPRINTLN(" Service, ready & waiting for connections...");
}

/*
  ===========================================================================================

  1. If not started OK then just re-print an error message for ever.
  2. Else
  3. Wait for a Bluetooth server to connect to us & set LED to Blue.
  4. While the server is connected publish Accelerometer readings every <interval> ms
  5. When server breaks connection, stop sending updates & set LED to Green

  ===========================================================================================
*/
void loop() {
  /* If main set-up has *all* completed OK then wait for listeners and when they connect
     transmit new accelerometer readings to them every <sample_interval> milliseconds
  */
  if (started_ok) {
    // wait for a BLE central
    BLEDevice central = BLE.central();

    // if a central is connected to the peripheral:
    if (central) {
      DPRINT("Connected to central: ");
      DPRINTLN(central.address());// print the central's BT address:
      // turn on the LED to indicate the connection:
      rgb_led.blue();

      /* Refresh and Bluetooth publish the accelerometer readings every <interval> ms
        but only while the central is connected:
      */
      while (central.connected()) {
        long currentMillis = millis();
        // if define ms have passed, re-send latest accelerometer values:
        if (currentMillis - previousMillis >= sample_interval) {
          previousMillis = currentMillis;
          DPRINT("New Reading: ");
          char acc_reading_as_buf[ble_message_len];
          accelerometer_readings->get_current_reading_to_ascii_buffer(acc_reading_as_buf, ble_message_len);
          DPRINTLN(acc_reading_as_buf); // buf is terminated like a c style str so ok to print here
          AccelXYZChar->writeValue(acc_reading_as_buf); // Server side will remove the terminator before decoding.
        }
      }
      // When the central disconnects, turn the LED back to green:
      rgb_led.green();
      DPRINT("Disconnected from central: ");
      DPRINTLN(central.address());
    }
  } else {
    // We can never escape from here we just keep reporting failure until the Arduion is reset
    DPRINTLN("Bluetooth data collector - Failed to start");
    delay(1000);
  }
}
