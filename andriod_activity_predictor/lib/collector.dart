import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';

/* Class to manage the process of collecting and saving accelerometer readings
   from the Arduino Nana
 */
class Collector {
  String _rootPath;
  String _recordFileName = "";
  File _recordFile;
  IOSink _recordFileSink;

  Collector() {
    /*
    Get the app path where we can write files.
     */
    _localPath.then((String rootPath) {
      _rootPath = rootPath;
    });
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
    print(_recordFileName);
    return;
  }

  /* Write a set of accelerometer readings as string to the record file
   */
  void writeReading(String readings) {
    if (_recordFileSink != null) {
      _recordFileSink.write(readings);
    }
    return;
  }

  /*
  Get the path where files can be written for this application.
   */
  Future<String> get _localPath async {
    final directory = await getExternalStorageDirectory();
    return directory.path;
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
}
