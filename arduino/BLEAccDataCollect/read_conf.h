#ifndef READ_CONF_H
#define READ_CONF_H

// https://github.com/bblanchon/ArduinoJson
#include <ArduinoJson.h>

class ReadConf  {
  public:
    /* BLE Connector Config
    */
    class BleConnectorConfig {
      public:
        String service_name; // The BLE Service name advertised by Arduino
        String service_uuid; // The BLE Service UUID
        String characteristic_uuid; // The BLE Characteristic UUID as required by Python Bluetooth lib.
        String characteristic_uuid_ble; // The BLE Characteristic UUIS as required by the Arduino BLE library
        int characteristic_len; // The number of bytes send as the Bluetooth message
        int sample_interval; // The number of milliseconds to wait between sending Accelerometer updates.
    };

  private:
    /* Member variables
    */
    const float doc_size_scaler = 1.5; // What % of additional working space JSON Deserialiser needs.    
    BleConnectorConfig _ble_connector_config;

    /* Methods
    */
    void _extract_ble_connector_config(JsonObject & config_doc);

  public:
    /* Methods to manage and extract different config objects.
    */
    ReadConf();
    bool begin();
    const BleConnectorConfig & get_ble_connector_config();
};

#endif // READ_CONF_H
