#include "read_conf.h"
#include "json_conf.h"
#include "debug_log.h"

/*
  The constructor expects there to be a global string defined called conf with an
  associated lenght variable called conf_len. These are supplied to the sketch via
  conf.h and conf.cpp which are in turn exported from the associated python project.

  The python project hosts the golden source conf.json which is exportd to conf.cpp
  as a string literal to be parsed here inte sketch. This means the python project and
  all associated sketechs share the exact same config without the need to link them via
  global constants defined in both places.
*/
ReadConf::ReadConf() {
  return;
}

/*
  Parse the JSON held in the global string whihc is the JSOn config exported from
  host python project.
*/
bool ReadConf::begin() {
  /* The document needs to be bigger that the raw JSOn as it is also teh working area
     for the Deserialiser. You can do an exact size by cutting the JSON here
     https://arduinojson.org/v6/assistant/. Or it looks to be a safe bet that increasing
     by about 50% gives a safe working margin.
  */
  DynamicJsonDocument doc(int(this->doc_size_scaler * json_conf_len));
  DeserializationError error = deserializeJson(doc, json_conf);
  bool is_ok = false;
  if (!error) {
    JsonObject config_doc = doc.as<JsonObject>();
    /* Extract all of the config objects into their respective member variables.
    */
    this->_extract_ble_connector_config(config_doc);
    this->_extract_ble_predictor_config(config_doc);
    this->_extract_ble_cnn_config(config_doc);
    this->_extract_ble_classes(config_doc);
    is_ok = true;
  } else {
    DPRINT("Failed to parse JSON with error: ");
    DPRINTLN(error.c_str());
  }

  return is_ok;
}

/*
    Extract the config settings just for the BLE Collector and populate the
    members of the private BleConnectorConfig member.
*/
void ReadConf::_extract_ble_connector_config(JsonObject & config_doc) {
  this->_ble_connector_config.service_name = config_doc["ble_collector"]["service_name"].as<String>();
  this->_ble_connector_config.service_uuid = config_doc["ble_collector"]["service_uuid"].as<String>();
  this->_ble_connector_config.characteristic_uuid = config_doc["ble_collector"]["characteristic_uuid"].as<String>();
  this->_ble_connector_config.characteristic_uuid_ble = config_doc["ble_collector"]["characteristic_uuid_ble"].as<String>();
  this->_ble_connector_config.characteristic_len = config_doc["ble_collector"]["characteristic_len"].as<String>().toInt();
  this->_ble_connector_config.sample_interval = config_doc["ble_collector"]["sample_interval"].as<String>().toInt();
  return;
}

const ReadConf::BleConnectorConfig & ReadConf::get_ble_connector_config() {
  return this->_ble_connector_config;
}

/*
  Extract the config settings just for the BLE Activity Predictor and populate the
  members of the private BlePredictorConfig member.
*/
void ReadConf::_extract_ble_predictor_config(JsonObject & config_doc) {
  this->_ble_predictor_config.service_name = config_doc["ble_predictor"]["service_name"].as<String>();
  this->_ble_predictor_config.service_uuid = config_doc["ble_predictor"]["service_uuid"].as<String>();
  this->_ble_predictor_config.characteristic_uuid = config_doc["ble_predictor"]["characteristic_uuid"].as<String>();
  this->_ble_predictor_config.characteristic_uuid_ble = config_doc["ble_predictor"]["characteristic_uuid_ble"].as<String>();
  this->_ble_predictor_config.characteristic_len = config_doc["ble_predictor"]["characteristic_len"].as<String>().toInt();
  this->_ble_predictor_config.sample_interval = config_doc["ble_predictor"]["sample_interval"].as<String>().toInt();
  this->_ble_predictor_config.predict_interval = config_doc["ble_predictor"]["predict_interval"].as<String>().toInt();
  return;
}

const ReadConf::BlePredictorConfig & ReadConf::get_ble_predictor_config() {
  return this->_ble_predictor_config;
}

/*
   Extract config settings for the CNN Model.
*/
void ReadConf::_extract_ble_cnn_config(JsonObject & config_doc) {
  this->_ble_cnn_config.look_back_window_size = config_doc["cnn"]["look_back_window_size"].as<String>().toInt();
  this->_ble_cnn_config.num_features = config_doc["cnn"]["num_features"].as<String>().toInt();
  this->_ble_cnn_config.arena_size = config_doc["cnn"]["tf_lite"]["arena_size"].as<String>().toInt();
  return;
}

const ReadConf::BleCNNConfig & ReadConf::get_ble_cnn_config() {
  return this->_ble_cnn_config;
}

/*
  Extract the names of the classification classes
*/
void ReadConf::_extract_ble_classes(JsonObject & config_doc) {
  int i = 0;
  while (config_doc["classes"][i]["class_name"].as<String>() != String("null")) {
    i++;
  }
  this->_ble_classes.num_classes = i;
  this->_ble_classes.class_names = (char **)malloc(sizeof(char *) * this->_ble_classes.num_classes);
  for (int j = 0; j < i; j++) {
    String s = config_doc["classes"][j]["class_name"].as<String>();
    this->_ble_classes.class_names[j] = (char *)malloc(s.length() + 1);
    strcpy(this->_ble_classes.class_names[j], s.c_str());
  }
  return;
}

const ReadConf::BleClassesConf & ReadConf::get_ble_classes_config() {
  return this->_ble_classes;
}
