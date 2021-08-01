import 'dart:convert';
import 'dart:math';
import 'package:activity_manager/collector.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_blue/flutter_blue.dart';

void main() async {
  runApp(ActivityManager());
}

class ActivityManager extends StatelessWidget {
  /*
  We need to load the JSON config before starting the App. For this we
  need a FutureBuilder as the return from loading the config is async.
  So here we wait on loading the JSON and when done we build the
  landing page with the config cascaded as a parameter.
   */
  Widget _futureBuildLandingPage(BuildContext context) {
    return Center(
      child: FutureBuilder<Map<String, dynamic>>(
        future: _loadJsonConfig(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.done) {
            print("Loaded Config");
            return _buildLandingPage(context, snapshot.data);
          } else {
            print("Pending load of initial config");
            return CircularProgressIndicator();
          }
        },
      ),
    );
  }

  Widget _buildLandingPage(BuildContext context, Map<String, dynamic> conf) {
    return MaterialApp(
      title: 'Arduino BLE Activity Manager',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: MyHomePage(title: 'Arduino BLE Activity Manager', conf: conf),
    );
  }

  /* Build the landing page after loading the JSON config.
   */
  @override
  Widget build(BuildContext context) {
    return _futureBuildLandingPage(context);
  }

  /* This App needs to share configuration with Python and Arduino sketches
     So we copy the common JSON file as an asset so it can be loaded and
     decoded here.
     This is async so we call it via a waiting call to FutureBuilder.
   */
  Future<Map<String, dynamic>> _loadJsonConfig() async {
    return await rootBundle
        .loadString("assets/json/conf.json")
        .then((jsonStr) => json.decode(jsonStr));
  }
}

class MyHomePage extends StatefulWidget {
  MyHomePage({Key key, this.title, this.conf}) : super(key: key);

  final Map<String, dynamic> conf;
  final String title;
  final FlutterBlue flutterBlue = FlutterBlue.instance;
  final List<BluetoothDevice> arduinoDevicesList = [];
  final List<BluetoothDevice> otherDevicesList = [];
  final Map<Guid, List<int>> readValues = new Map<Guid, List<int>>();

  @override
  _MyHomePageState createState() => _MyHomePageState(conf: conf);
}

class _MyHomePageState extends State<MyHomePage> {
  _MyHomePageState({this.conf});

  final Map<String, dynamic> conf; // JSON Config

  BluetoothDevice _connectedDevice; // The BLE we are connected to
  BluetoothCharacteristic _connectedCharacteristic; // The live characteristic
  int _characteristicMTULength;
  List<BluetoothService> _services;
  List<String> _activityDevices = [];

  bool _connecting = false; // Is BLE connection in progress
  String _predictorName = ""; // Name of Arduino BLE Predictor service
  String _predictorCharacteristicName = "";
  String _prediction = ""; // The decoded BLE prediction message
  Stream<List<int>> _predictionStream; // The BLE prediction stream
  Map<String, String> _predictionClassToColour = {};

  String _collectorName = ""; // Name of Arduino BLE Collector service
  String _collectorCharacteristicName = "";
  Stream<List<int>> _collectionStream; // The BlE accelerometer stream
  String _accelerometerReadings = "";
  final String csvHeaderRow =
      "index,accel_x,accel_y,accel_z"; // ToDo: move to json Conf
  String _readings = "";
  List<String> _classTypes = [];
  String _classToRecord = "";
  bool _recording = false;
  String _mode = "";
  String _buttonAction = "";
  Collector _collector = new Collector();

  /* This is called for every Bluetooth device that is currently advertising
     itself. If the device name matches one of our expected Arduino device
     names then add it to the list of devices that can be connected to.
   */
  _addDeviceTolist(final BluetoothDevice device) {
    if (!widget.arduinoDevicesList.contains(device)) {
      setState(() {
        if (_activityDevices.contains(device.name)) {
          if (!widget.arduinoDevicesList.contains(device)) {
            widget.arduinoDevicesList.add(device);
          }
        } else {
          if (!widget.otherDevicesList.contains(device)) {
            widget.otherDevicesList.add(device);
          }
        }
      });
    }
  }

  @override
  void initState() {
    super.initState();

    /*
    From the already loaded JSON config extract key details.
     */
    setState(() {
      int predictorCharacteristicLen;
      int collectorCharacteristicLen;

      _predictorName = conf["ble_predictor"]["service_name"].toString();
      _predictorCharacteristicName =
          conf["ble_predictor"]["characteristic_uuid"].toString() +
              conf["ble_predictor"]["ble_base_uuid"].toString();
      _predictorCharacteristicName = _predictorCharacteristicName.toLowerCase();
      predictorCharacteristicLen = conf["ble_predictor"]["characteristic_len"];

      _collectorName = conf["ble_collector"]["service_name"].toString();
      _collectorCharacteristicName =
          conf["ble_collector"]["characteristic_uuid"].toString() +
              conf["ble_collector"]["ble_base_uuid"].toString();
      _collectorCharacteristicName = _collectorCharacteristicName.toLowerCase();
      collectorCharacteristicLen = conf["ble_collector"]["characteristic_len"];
      _characteristicMTULength =
          max(collectorCharacteristicLen, predictorCharacteristicLen);

      for (dynamic predictionClass in conf["classes"]) {
        _predictionClassToColour[predictionClass["class_name"]] =
            predictionClass["colour"];
        _classTypes.add(predictionClass["class_name"]);
      }
      _activityDevices.add(_collectorName);
      _activityDevices.add(_predictorName);
    });

    /* Create list of valid Activity device names that we will allow
    connection to so we can interact with the respective Arduino sketch.
    This is used to filter the list of all Bluetooth devices visible so
    we can identify just the ones that are our target Arduino devices.
     */
    widget.flutterBlue.connectedDevices
        .asStream()
        .listen((List<BluetoothDevice> devices) {
      for (BluetoothDevice device in devices) {
        _addDeviceTolist(device);
      }
    });
    widget.flutterBlue.scanResults.listen((List<ScanResult> results) {
      for (ScanResult result in results) {
        _addDeviceTolist(result.device);
      }
    });
    widget.flutterBlue.startScan();
  }

  /*
  View that shows a list of all Bluetooth devices separated into
  Arduino services we can connect to and other visible Bluetooth
  devices.

  For the services we can connect to we show a "connect" button
  that connects to the specific device. We then set the connected
  device global to that device. Then based on the type of device we
  have connected to Predictor or Collector a specialised view will
  be show allowing for that specific interaction.
   */
  Widget _buildListViewOfDevices() {
    List<Container> arduinoContainers = [];
    List<Container> otherContainers = [];

    for (BluetoothDevice device in widget.arduinoDevicesList) {
      arduinoContainers.add(
        Container(
          height: 50,
          child: Row(
            children: <Widget>[
              Expanded(
                child: Column(
                  children: <Widget>[
                    Text(device.name == '' ? '(unknown device)' : device.name),
                    Text(device.id.toString()),
                  ],
                ),
              ),
              TextButton(
                style: ButtonStyle(
                  backgroundColor:
                      MaterialStateProperty.all<Color>(Colors.blue),
                ),
                child: Text(
                  _connecting ? 'Connecting' : 'connect',
                  style: TextStyle(color: Colors.white),
                ),
                onPressed: () async {
                  widget.flutterBlue.stopScan();
                  try {
                    setState(() {
                      _connecting = true;
                    });
                    await device.connect();
                    await device.requestMtu(_characteristicMTULength);
                  } catch (e) {
                    if (e.code != 'already_connected') {
                      throw e;
                    }
                  } finally {
                    _services = await device.discoverServices();
                  }
                  setState(() {
                    _connectedDevice = device;
                  });
                },
              ),
            ],
          ),
        ),
      );
    }

    for (BluetoothDevice device in widget.otherDevicesList) {
      otherContainers.add(
        Container(
          height: 50,
          child: Row(
            children: <Widget>[
              Expanded(
                child: Column(
                  children: <Widget>[
                    Text(device.name == '' ? '(unknown device)' : device.name),
                    Text(device.id.toString()),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      children: [
        Padding(
          padding: EdgeInsets.all(8),
          child:
              Text("Activity Manager Devices", style: TextStyle(fontSize: 20)),
        ),
        Image(image: AssetImage("assets/images/arduino.png")),
        Divider(height: 20, thickness: 2, indent: 20, endIndent: 20),
        Container(
          height: 150,
          child: ListView(
            padding: const EdgeInsets.all(8),
            children: <Widget>[
              ...arduinoContainers,
            ],
          ),
        ),
        Divider(height: 20, thickness: 2, indent: 20, endIndent: 20),
        Padding(
          padding: EdgeInsets.all(8),
          child:
              Text("Other Bluetooth Devices", style: TextStyle(fontSize: 20)),
        ),
        Container(
          height: 150,
          child: ListView(
            padding: const EdgeInsets.all(8),
            children: <Widget>[
              ...otherContainers,
            ],
          ),
        ),
      ],
    );
  }

  /* Convert the predicted activity class name to the image of the
     arduino board with the colour LED set to the corresponding colour. If
     there is no mapping return the default images showing LED as off.
   */
  Image _classToImage(String className) {
    String base = "arduino";
    if (_predictionClassToColour.containsKey(className)) {
      base = base + "-" + _predictionClassToColour[className];
    }
    return Image(image: AssetImage("assets/images/" + base + ".png"));
  }

  /* Iterate all services to find the service that contains the specific
     notification characteristic used to transmit the BLE message for
     the given characteristic name
  */
  void _findAndSetCharacteristic(String characteristicNameToFind) {
    if (_connectedCharacteristic == null) {
      for (BluetoothService service in _services) {
        /* Iterate the service characteristics and when (if) we find the
           notify characteristic
       */
        for (BluetoothCharacteristic characteristic
            in service.characteristics) {
          /* If we haven't found the characteristic and the characteristic
             bring iterated matched the Predictor notify characteristic UUID
             set the connected characteristic.
           */
          if (_connectedCharacteristic == null) {
            if (characteristic.uuid.toString() == characteristicNameToFind) {
              setState(() {
                _connectedCharacteristic = characteristic;
              });
            }
          }
        }
      }
    }
  }

  /* View specific to the Predictor device that is streaming movement
     predictions. This view just shows the current prediction being
     transmitted by the Arduino device that is running the movement
     Neural net locally using tensor flow lite.
   */
  Widget _buildPredictorDeviceView() {
    _findAndSetCharacteristic(_predictorCharacteristicName);

    setState(() {
      _prediction = "----------";
    });
    if (_connectedCharacteristic != null && _connectedDevice != null) {
      if (_connectedCharacteristic.properties.notify) {
        if (!_connectedCharacteristic.isNotifying) {
          () async {
            await _connectedCharacteristic.setNotifyValue(true);
            setState(() {
              if (_connectedCharacteristic != null) {
                _predictionStream = _connectedCharacteristic.value;
                _predictionStream = _predictionStream.asBroadcastStream();
              }
            });
          }();
        }
      } else {
        setState(() {
          _prediction = "Error: not notifiable";
        });
      }
    } else {
      setState(() {
        _prediction = "Error: no characteristic";
      });
    }

    return StreamBuilder<List<int>>(
        stream: _predictionStream,
        builder: (BuildContext context, AsyncSnapshot<dynamic> snapshot) {
          if (snapshot.hasError) {
            _prediction = "**Error**";
          } else {
            if (snapshot.data != null) {
              _prediction = utf8.decode(snapshot.data).trim();
            } else {
              _prediction = "Disconnected";
            }
          }
          return Column(
            children: [
              Padding(
                padding: EdgeInsets.all(8),
                child:
                    Text("Activity Predictor", style: TextStyle(fontSize: 20)),
              ),
              _classToImage(_prediction),
              Divider(height: 20, thickness: 2, indent: 20, endIndent: 20),
              Padding(
                padding: EdgeInsets.all(8),
                child: Column(
                  children: [
                    Text("Prediction", style: TextStyle(fontSize: 20)),
                    Text(_prediction, style: TextStyle(fontSize: 20)),
                  ],
                ),
              ),
              Divider(height: 20, thickness: 2, indent: 20, endIndent: 20),
              ButtonTheme(
                minWidth: 10,
                height: 20,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: ElevatedButton(
                    style: ButtonStyle(
                      backgroundColor:
                          MaterialStateProperty.all<Color>(Colors.red),
                    ),
                    child:
                        Text('Cancel', style: TextStyle(color: Colors.white)),
                    onPressed: () async {
                      setState(() {
                        _connectedDevice = null;
                      });
                      if (_connectedDevice != null) {
                        await _connectedDevice.disconnect();
                      }
                    },
                  ),
                ),
              ),
            ],
          );
        });
  }

  /*
  View specific to the Collector device that is streaming accelerometer
  readings. This view confirms the type of activity being recorded and
  then records the streams readings to a file. This file can then later
  be used by the Python parent training project as training or validation
  data.
   */
  Widget _buildCollectorDeviceView() {
    _findAndSetCharacteristic(_collectorCharacteristicName);

    setState(() {
      _prediction = "----------";
    });
    if (_connectedCharacteristic != null && _connectedDevice != null) {
      if (_connectedCharacteristic.properties.notify) {
        if (!_connectedCharacteristic.isNotifying) {
          () async {
            await _connectedCharacteristic.setNotifyValue(true);
            _connectedCharacteristic.value.listen((value) {
              print(utf8.decode(value));
            });
            setState(() {
              if (_connectedCharacteristic != null) {
                _collectionStream = _connectedCharacteristic.value;
                _collectionStream = _collectionStream
                    .asBroadcastStream(); // Support multi listen
              }
            });
          }();
        }
      } else {
        setState(() {
          _readings = "Error: not notifiable";
        });
      }
    } else {
      setState(() {
        _readings = "Error: no characteristic";
      });
    }

    if (!_recording) {
      _mode = "Listening";
      _buttonAction = "Start Recording";
    } else {
      _mode = "Recording";
      _buttonAction = "Stop Recording";
    }

    if (_classToRecord.length == 0) {
      _classToRecord = _classTypes[0];
    }

    return StreamBuilder<List<int>>(
        stream: _collectionStream,
        builder: (BuildContext context, AsyncSnapshot<dynamic> snapshot) {
          if (snapshot.hasError) {
            _readings = "**Error**";
          } else {
            if (snapshot.data != null) {
              _readings = utf8.decode(snapshot.data).trim();
              if (_recording) {
                _collector.writeReading(_readings);
              }
            } else {
              _readings = "Disconnected";
            }
          }
          return Column(
            children: [
              Padding(
                padding: EdgeInsets.all(8),
                child:
                    Text("Activity Collector", style: TextStyle(fontSize: 20)),
              ),
              Image(image: AssetImage("assets/images/arduino.png")),
              Divider(height: 20, thickness: 2, indent: 20, endIndent: 20),
              Padding(
                padding: EdgeInsets.all(8),
                child: Column(
                  children: [
                    Text("Activity to Record", style: TextStyle(fontSize: 20)),
                    DropdownButton<String>(
                        style: TextStyle(fontSize: 20, color: Colors.black),
                        value: _classToRecord,
                        onChanged: _recording
                            ? null // cannot change class while recording
                            : (String newValue) {
                                setState(() {
                                  _classToRecord = newValue;
                                });
                              },
                        items: _classTypes
                            .map<DropdownMenuItem<String>>((String value) {
                          return DropdownMenuItem<String>(
                            value: value,
                            child: Text(value),
                          );
                        }).toList()),
                    Text(_mode, style: TextStyle(fontSize: 20)),
                    Text(_readings, style: TextStyle(fontSize: 20)),
                    ElevatedButton(
                      style: ButtonStyle(
                        backgroundColor:
                            MaterialStateProperty.all<Color>(Colors.blue),
                      ),
                      child: Text(_buttonAction,
                          style: TextStyle(color: Colors.white)),
                      onPressed: () async {
                        setState(() {
                          _recording = !_recording;
                        });
                        if (_recording) {
                          _collector.newRecordFile(_classToRecord);
                        }
                      },
                    ),
                  ],
                ),
              ),
              Divider(height: 20, thickness: 2, indent: 20, endIndent: 20),
              ButtonTheme(
                minWidth: 10,
                height: 20,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: ElevatedButton(
                    style: ButtonStyle(
                      backgroundColor:
                          MaterialStateProperty.all<Color>(Colors.red),
                    ),
                    child:
                        Text('Cancel', style: TextStyle(color: Colors.white)),
                    onPressed: () async {
                      setState(() {
                        _connectedDevice = null;
                      });
                      if (_connectedDevice != null) {
                        await _connectedDevice.disconnect();
                      }
                    },
                  ),
                ),
              ),
            ],
          );
        });
  }

  Widget _buildView() {
    if (_connectedDevice != null) {
      setState(() {
        _connecting = false; // have connected to main device at this point
      });
      if (_connectedDevice.name == _predictorName) {
        return _buildPredictorDeviceView();
      } else {
        return _buildCollectorDeviceView(); // ToDo: explicit 'if' for collector
      } // ToDo: Add unknown view if neither collector nor predictor
    }
    return _buildListViewOfDevices();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: Text(widget.title),
        ),
        body: _buildView(),
      );
}
