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
  BluetoothCharacteristic _ConnectedCharacteristic;
  List<BluetoothService> _services;
  List<String> _activityDevices = [];

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
    _activityDevices.add(conf["ble_collector"]["ble_collector"]);
    _activityDevices.add(conf["ble_collector"]["service_name"]);

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
                  'Connect',
                  style: TextStyle(color: Colors.white),
                ),
                onPressed: () async {
                  widget.flutterBlue.stopScan();
                  try {
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

  List<ButtonTheme> _buildNotifyButton(BluetoothCharacteristic characteristic) {
    List<ButtonTheme> buttons = [];

    if (characteristic.properties.notify) {
      buttons.add(
        ButtonTheme(
          minWidth: 10,
          height: 20,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: ElevatedButton(
              style: ButtonStyle(
                backgroundColor: MaterialStateProperty.all<Color>(Colors.green),
              ),
              child: Text('NOTIFY', style: TextStyle(color: Colors.white)),
              onPressed: () async {
                characteristic.value.listen((value) {
                  widget.readValues[characteristic.uuid] = value;
                  print(utf8.decode(value));
                });
                if (_ConnectedCharacteristic != null) {
                  await characteristic.setNotifyValue(false);
                  _ConnectedCharacteristic = null;
                }
                _ConnectedCharacteristic = characteristic;
                await characteristic.setNotifyValue(true);
              },
            ),
          ),
        ),
      );
    }

    return buttons;
  }

  ListView _buildConnectDeviceView() {
    List<Container> containers = [];

    for (BluetoothService service in _services) {
      List<Widget> characteristicsWidget = [];

      for (BluetoothCharacteristic characteristic in service.characteristics) {
        characteristicsWidget.add(
          Align(
            alignment: Alignment.centerLeft,
            child: Column(
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Text(characteristic.uuid.toString(),
                        style: TextStyle(fontWeight: FontWeight.bold)),
                  ],
                ),
                Row(
                  children: <Widget>[
                    ..._buildNotifyButton(characteristic),
                  ],
                ),
                Row(
                  children: <Widget>[
                    Text('Value: ' +
                        widget.readValues[characteristic.uuid].toString()),
                  ],
                ),
                Divider(),
              ],
            ),
          ),
        );
      }
      containers.add(
        Container(
          child: ExpansionTile(
              title: Text(service.uuid.toString()),
              children: characteristicsWidget),
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.all(8),
      children: <Widget>[
        ...containers,
      ],
    );
  }

  Widget _buildView() {
    print("Tick");
    if (_connectedDevice != null) {
      return _buildConnectDeviceView();
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
