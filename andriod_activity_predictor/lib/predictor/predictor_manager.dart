import 'dart:convert';

/* Class to manage the process of displaying model predictions from the
  Arduino Nano
 */
class PredictorManager {
  String _predictorName = ""; // Name of Arduino BLE Predictor service
  String _predictorCharacteristicName = "";
  int _predictorCharacteristicLen;

  /* Prevent default construction
   */
  PredictorManager._();

  /* Boot strap the class given the JSOn config.
   */
  PredictorManager.from(Map<String, dynamic> jsonConfig) {
    _predictorName = jsonConfig["ble_predictor"]["service_name"].toString();
    _predictorCharacteristicName = jsonConfig["ble_predictor"]
                ["characteristic_uuid"]
            .toString()
            .toLowerCase() +
        jsonConfig["ble_predictor"]["ble_base_uuid"].toString().toLowerCase();
    _predictorCharacteristicLen =
        jsonConfig["ble_predictor"]["characteristic_len"];
  }

  String get predictorCharacteristicName {
    return _predictorCharacteristicName;
  }

  String get predictorName {
    return _predictorName;
  }

  int get predictorCharacteristicLen {
    return _predictorCharacteristicLen;
  }

  static String decode(List<int> byteCode) {
    return utf8.decode(byteCode).trim();
  }
}
