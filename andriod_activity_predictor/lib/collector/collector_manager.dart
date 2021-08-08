import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'package:flutter_file_manager/flutter_file_manager.dart';

/* Class to manage the process of collecting and saving accelerometer readings
   from the Arduino Nano
 */
class CollectorManager {
  String _rootPath;
  String _recordFileName = "";
  File _recordFile;
  IOSink _recordFileSink;
  static int _idx = 0;
  static final String _csvHeaderRow = "index,accel_x,accel_y,accel_z\n";
  String _collectorName; // Name of Arduino BLE Collector service
  String _collectorCharacteristicName;
  int _collectorCharacteristicLen;

  /* Prevent default construction
   */
  CollectorManager._();

  /* Boot strap the class given the JSOn config.
   */
  CollectorManager.from(Map<String, dynamic> jsonConfig) {
    /*
    Get the app path where we can write files.
     */
    _localPath.then((String rootPath) {
      _rootPath = rootPath;
    });
    _collectorName = jsonConfig["ble_collector"]["service_name"].toString();
    _collectorCharacteristicName = jsonConfig["ble_collector"]
                ["characteristic_uuid"]
            .toString().toLowerCase() +
        jsonConfig["ble_collector"]["ble_base_uuid"].toString().toLowerCase();
    _collectorCharacteristicLen =
        jsonConfig["ble_collector"]["characteristic_len"];
  }

  String get collectorCharacteristicName {
    return _collectorCharacteristicName;
  }

  String get collectorName {
    return _collectorName;
  }

  int get collectorCharacteristicLen {
    return _collectorCharacteristicLen;
  }

  String get currentRecordFileName {
    return _recordFileName.split('/').last;
  }

  /* Close the current record file if open and create a new file for
     the given activity class.
   */
  void newRecordFile(String className) {
    _recordFileName = _getNewRecordFileName(className);
    if (_recordFileSink != null) {
      _recordFileSink.close();
    }
    _recordFile = File(_recordFileName);
    _recordFileSink =
        _recordFile.openWrite(mode: FileMode.writeOnlyAppend, encoding: utf8);
    _recordFileSink.write(_csvHeaderRow);
    return;
  }

  /* If there is an open record file close it.
   */
  void closeRecordFile() {
    if (_recordFileSink != null) {
      _recordFileSink.close();
      _recordFileSink = null;
    }
    _idx = 0;
    return;
  }

  /* Write a set of accelerometer readings as string to the record file
   */
  String writeReading(String readings) {
    String res = _idx.toString() + "," + readings;
    _idx += 1;
    if (_recordFileSink != null) {
      // Need to add a index column to the readings.
      _recordFileSink.write(res + "\n");
    }
    return res;
  }

  static String _removeLastCharacterIfComma(String str) {
    String res;
    if ((str != null) && (str.length > 0)) {
      if ("," == str.substring(str.length - 1)) {
        res = str.substring(0, str.length - 1);
      }
    }
    return res;
  }

  /* Create a new record file name based on the given class and the
      current timestamp.
   */
  String _getNewRecordFileName(String className) {
    String fn = "";
    DateTime now = new DateTime.now();
    if (_rootPath.length > 0) {
      fn = join(
          _rootPath,
          className +
              '_' +
              now.year.toString() +
              '_' +
              now.month.toString() +
              '_' +
              now.day.toString() +
              '_' +
              now.hour.toString() +
              '_' +
              now.minute.toString() +
              '_' +
              now.second.toString() +
              '.csv');
    }
    return fn;
  }

  /* Get the list of saved collection files.
   */
  Future<List<String>> listSavedCollectorFiles() async {
    List<String> savedFileList = [];
    await FileManager.listFiles(_rootPath).then((List<File> files) => {
          for (File f in files)
            {
              savedFileList
                  .add(f.toString().replaceAll("'", "").split('/').last)
            }
        });
    return savedFileList;
  }

  /*
  Get the path where files can be written for this application.
   */
  Future<String> get _localPath async {
    final directory = await getExternalStorageDirectory();
    return directory.path;
  }

  /* Convert the BLE bytecode into a String and replace the semicolon
  separators with comma so the result can be saved as a s row in teh target
  csv file.
   */
  static String decodeReadings(List<int> readingsAsByteCode) {
    return _removeLastCharacterIfComma(
        utf8.decode(readingsAsByteCode).trim().replaceAll(";", ","));
  }
}
