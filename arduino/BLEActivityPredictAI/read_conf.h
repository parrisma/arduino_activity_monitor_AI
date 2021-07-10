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

    /* BLE Predictor Config
    */
    class BlePredictorConfig {
      public:
        String service_name; // The BLE Service name advertised by Arduino
        String service_uuid; // The BLE Service UUID
        String characteristic_uuid; // The BLE Characteristic UUID as required by Python Bluetooth lib.
        String characteristic_uuid_ble; // The BLE Characteristic UUIS as required by the Arduino BLE library
        int characteristic_len; // The number of bytes send as the Bluetooth message
        int sample_interval; // The number of milliseconds to wait between sending Accelerometer updates.
        int predict_interval; // The number of millseconds between model predictions
    };

    /* CNN Model Config
    */
    class BleCNNConfig {
      public:
        int look_back_window_size; // The number of readings needed for a prediction
        int num_features; // The number of features passed to model e.g. x,y,z, accelerometer readings
        int arena_size; // Number of bytes to allocate for TF Lite Tensor Arena.
    };

    /* Classification classes
    */
    class BleClassesConf {
      public:
        int num_classes;
        char ** class_names; // Dynamically allocated array of string
    };
  private:
    /* Member variables
    */
    const float doc_size_scaler = 1.5; // What % of additional working space JSON Deserialiser needs.
    BleConnectorConfig _ble_connector_config;
    BlePredictorConfig _ble_predictor_config;
    BleCNNConfig _ble_cnn_config;
    BleClassesConf _ble_classes;

    /* Methods
    */
    void _extract_ble_connector_config(JsonObject & config_doc);
    void _extract_ble_predictor_config(JsonObject & config_doc);
    void _extract_ble_cnn_config(JsonObject & config_doc);
    void _extract_ble_classes(JsonObject & config_doc);

  public:
    /* Methods to manage and extract different config objects.
    */
    ReadConf();
    bool begin();
    const BleConnectorConfig & get_ble_connector_config();
    const BlePredictorConfig & get_ble_predictor_config();
    const BleCNNConfig & get_ble_cnn_config();
    const BleClassesConf & get_ble_classes_config();
};

#endif // READ_CONF_H
