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
        String service_name;
        String service_uuid;
        String characteristic_uuid;
        int characteristic_len;
        int sample_interval;
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
