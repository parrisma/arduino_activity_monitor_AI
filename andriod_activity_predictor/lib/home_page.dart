import 'dart:math';
import 'package:activity_manager/collector/collector_manager.dart';
import 'package:activity_manager/predictor/predictor_manager.dart';
import 'package:activity_manager/bluetooth/bluetooth_manager.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_blue/flutter_blue.dart';

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

  BluetoothManager _bluetoothManager;

  String _prediction = ""; // The decoded BLE prediction message
  Stream<List<int>> _predictionStream; // The BLE prediction stream
  Map<String, String> _predictionClassToColour = {};
  PredictorManager _predictorManager;

  Stream<List<int>> _collectionStream; // The BlE accelerometer stream
  String _readings = "";
  List<String> _classTypes = [];
  String _classToRecord = "";
  bool _recording = false;
  String _mode = "";
  String _buttonAction = "";
  Future<List<String>> _collectorFileList;
  CollectorManager _collectorManager;

  /* This is called for every Bluetooth device that is currently advertising
     itself. If the device name matches one of our expected Arduino device
     names then add it to the list of devices that can be connected to.
   */
  _addDeviceTolist(final BluetoothDevice device) {
    if (!widget.arduinoDevicesList.contains(device)) {
      setState(() {
        if (_bluetoothManager.deviceIsArduinoNanoActivityDevice(device.name)) {
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
      _bluetoothManager = new BluetoothManager.from(conf);
      _predictorManager = new PredictorManager.from(conf);
      _collectorManager = new CollectorManager.from(conf);

      _bluetoothManager.characteristicMTULength = max(
          _collectorManager.collectorCharacteristicLen,
          _predictorManager.predictorCharacteristicLen);

      _bluetoothManager.registerArduinoNanoActivityDevice(
          _collectorManager.collectorName, _buildCollectorDeviceView);
      _bluetoothManager.registerArduinoNanoActivityDevice(
          _predictorManager.predictorName, _buildPredictorDeviceView);

      for (dynamic predictionClass in conf["classes"]) {
        _predictionClassToColour[predictionClass["class_name"]] =
            predictionClass["colour"];
        _classTypes.add(predictionClass["class_name"]);
      }
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

    setState(() {});

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
              _bluetoothManager.connecting
                  ? Container(
                      child: CircularProgressIndicator(
                        backgroundColor: Colors.white,
                      ),
                    )
                  : TextButton(
                      style: ButtonStyle(
                        backgroundColor:
                            MaterialStateProperty.all<Color>(Colors.blue),
                      ),
                      child: Text(
                        'connect',
                        style: TextStyle(color: Colors.white),
                      ),
                      onPressed: () async {
                        widget.flutterBlue.stopScan();
                        await _bluetoothManager.connect(device);
                        setState(() {});
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

  /* View specific to the Predictor device that is streaming movement
     predictions. This view just shows the current prediction being
     transmitted by the Arduino device that is running the movement
     Neural net locally using tensor flow lite.
   */
  Widget _buildPredictorDeviceView() {
    if (!_bluetoothManager.isCharacteristicStreamLive(
        _collectorManager.collectorCharacteristicName)) {
      () async {
        _predictionStream = await _bluetoothManager
            .getActivityStream(_predictorManager.predictorCharacteristicName);
        setState(() {});
      }();
    }

    return StreamBuilder<List<int>>(
        stream: _predictionStream,
        builder: (BuildContext context, AsyncSnapshot<dynamic> snapshot) {
          if (snapshot.hasError) {
            _prediction = "**Error**";
          } else {
            if (snapshot.data != null) {
              _prediction = PredictorManager.decode(snapshot.data);
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
                      await _bluetoothManager.disconnect();
                      setState(() {});
                      widget.flutterBlue.startScan();
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
    if (!_bluetoothManager.isCharacteristicStreamLive(
        _collectorManager.collectorCharacteristicName)) {
      () async {
        _collectionStream = await _bluetoothManager
            .getActivityStream(_collectorManager.collectorCharacteristicName);
        setState(() {});
      }();
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

    if (_collectorFileList == null) {
      _collectorFileList = _collectorManager.listSavedCollectorFiles();
    }

    return StreamBuilder<List<int>>(
        stream: _collectionStream,
        builder: (BuildContext context, AsyncSnapshot<dynamic> snapshot) {
          if (snapshot.hasError) {
            _readings = "**Error**";
          } else {
            if (snapshot.data != null) {
              _readings = CollectorManager.decodeReadings(snapshot.data);
              if (_recording) {
                _readings = _collectorManager.writeReading(_readings);
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
                    Container(
                        margin: const EdgeInsets.all(3.0),
                        padding: const EdgeInsets.all(3.0),
                        decoration: BoxDecoration(
                            border: _recording
                                ? Border.all(color: Colors.red)
                                : Border.all(color: Colors.grey)),
                        child: Text(_readings, style: TextStyle(fontSize: 20))),
                    _recording
                        ? Text("Saving To", style: TextStyle(fontSize: 20))
                        : Text("Saved Files", style: TextStyle(fontSize: 20)),
                    Container(
                        height: 100,
                        margin: const EdgeInsets.all(15.0),
                        padding: const EdgeInsets.all(3.0),
                        decoration: BoxDecoration(
                            border: Border.all(color: Colors.grey)),
                        child: _recording
                            ? Text(_collectorManager.currentRecordFileName,
                                style: TextStyle(fontSize: 20))
                            : FutureBuilder(
                                future: _collectorFileList,
                                builder: (BuildContext context,
                                    AsyncSnapshot snapshot) {
                                  if (snapshot.connectionState ==
                                      ConnectionState.done) {
                                    return Scrollbar(
                                        thickness: 10,
                                        isAlwaysShown: true,
                                        child: ListView.builder(
                                            itemCount:
                                                snapshot.data?.length ?? 0,
                                            itemBuilder: (context, index) {
                                              return ListTile(
                                                title: Text(
                                                    snapshot.data[index],
                                                    style: TextStyle(
                                                        fontSize: 20)),
                                              );
                                            }));
                                  } else {
                                    return Center(
                                        child: Text("Loading",
                                            style: TextStyle(fontSize: 20)));
                                  }
                                },
                              )),
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
                          _collectorManager.newRecordFile(_classToRecord);
                        } else {
                          _collectorManager.closeRecordFile();
                          setState(() {
                            _collectorFileList =
                                _collectorManager.listSavedCollectorFiles();
                          });
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
                        _recording = false;
                      });
                      _collectorManager.closeRecordFile();
                      await _bluetoothManager.disconnect();
                      widget.flutterBlue.startScan();
                      setState(() {});
                    },
                  ),
                ),
              ),
            ],
          );
        });
  }

  /*
  Error View specific when the selected Arduino activity device name is
  not mapped to a handler view.
   */
  Widget _buildErrorDeviceView() {
    return Column(
      children: [
        Padding(
          padding: EdgeInsets.all(8),
          child:
              Text("Unknown Activity Device", style: TextStyle(fontSize: 20)),
        ),
        Image(image: AssetImage("assets/images/arduino.png")),
        Divider(height: 20, thickness: 2, indent: 20, endIndent: 20),
        Center(
            child: Padding(
          padding: EdgeInsets.all(10),
          child: Text(
              "Device type [" + _bluetoothManager.deviceName + "] not known",
              style: TextStyle(fontSize: 20, color: Colors.red)),
        )),
        ButtonTheme(
          minWidth: 10,
          height: 20,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: ElevatedButton(
              style: ButtonStyle(
                backgroundColor: MaterialStateProperty.all<Color>(Colors.red),
              ),
              child: Text('Cancel', style: TextStyle(color: Colors.white)),
              onPressed: () async {
                await _bluetoothManager.disconnect();
                widget.flutterBlue.startScan();
                setState(() {});
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildView() {
    /* If there is a connected BLE device build the view that is registered
       for that device. If device not registered show error view.
     */
    if (_bluetoothManager.connectedAndReady) {
      return _bluetoothManager.getDeviceViewBuilder(_buildErrorDeviceView)();
    }
    /* If no BLE device is connected show the BLE device explorer view that
       allows all BLE devices to be seen and the registered activity devices
       to be connected to.
     */
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
