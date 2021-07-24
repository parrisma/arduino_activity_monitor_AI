import 'dart:convert';

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

  final Map<String, dynamic> conf;
  BluetoothDevice _connectedDevice;
  BluetoothCharacteristic _connectedCharacteristic;
  List<BluetoothService> _services;
  List<String> _activityDevices = [];
  bool _connecting = false;
  String _predictorName = "";
  String _collectorName = "";
  String _predictorCharacteristicName = "";
  String _collectorCharacteristicName = "";
  String _prediction = "";
  Map<String, String> _predictionClassToColour = {};
  Stream<List<int>> _predictionStream;

  /* This is called for every Bluetooth device that is currently advertising
     itself. If the device name matches one of our expected Arduino device
     names then add it to the list of devices that can be connected to.
   */
  _addDeviceTolist(final BluetoothDevice device) {
    if (!widget.arduinoDevicesList.contains(device)) {
      setState(() {
        if (_activityDevices.contains(device.name)) {
          widget.arduinoDevicesList.add(device);
        } else {
          widget.otherDevicesList.add(device);
        }
      });
    }
  }

  @override
  void initState() {
    super.initState();

    /* Create list of valid Activity device names that we will allow
    connection to so we can interact with the respective Arduino sketch.
    This is used to filter the list of all Bluetooth devices visible so
    we can identify just the ones that are our target Arduino devices.
     */
    setState(() {
      _predictorName = conf["ble_predictor"]["service_name"].toString();
      _predictorCharacteristicName =
          conf["ble_predictor"]["characteristic_uuid"].toString() +
              conf["ble_predictor"]["ble_base_uuid"].toString();
      _predictorCharacteristicName = _predictorCharacteristicName.toLowerCase();

      _collectorName = conf["ble_collector"]["service_name"].toString();
      _collectorCharacteristicName =
          conf["ble_collector"]["characteristic_uuid"].toString() +
              conf["ble_predictor"]["ble_base_uuid"].toString();
      _collectorCharacteristicName = _collectorCharacteristicName.toLowerCase();

      for (dynamic predictionClass in conf["classes"]) {
        _predictionClassToColour[predictionClass["class_name"]] =
            predictionClass["colour"];
      }
      _activityDevices.add(_collectorName);
      _activityDevices.add(_predictorName);
    });

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

  /*
  Convert the predicted activity class name to the image of the
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

  /*
  View specific to the Predictor device that is streaming movement
  predictions. This view just shows the current prediction being
  transmitted by the Arduino device that is running the movement
  Neural net locally using tensor flow lite.
   */
  Widget _buildPredictorDeviceView() {
    /* Iterate all services to find the service that contains the specific
     notification characteristic used to transmit the neural net model
     prediction.
     */
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
            if (characteristic.uuid.toString() ==
                _predictorCharacteristicName) {
              _connectedCharacteristic = characteristic;
            }
          }
        }
      }
    }

    setState(() {
      _prediction = "----------";
    });
    if (_connectedCharacteristic != null && _connectedDevice != null) {
      if (_connectedCharacteristic.properties.notify) {
        () async {
          await _connectedCharacteristic.setNotifyValue(true);
          setState(() {
            if (_connectedCharacteristic != null) {
              _predictionStream = _connectedCharacteristic.value;
              _predictionStream = _predictionStream.asBroadcastStream();
            }
          });
        }();
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
        builder: (context, snapshot) {
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
                      if (_connectedDevice != null) {
                        await _connectedDevice.disconnect();
                      }
                      setState(() {
                        _connectedDevice = null;
                      });
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
        return _buildPredictorDeviceView();
      }
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
