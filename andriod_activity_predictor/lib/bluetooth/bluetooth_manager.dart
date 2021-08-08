import 'dart:collection';
import 'package:flutter_blue/flutter_blue.dart';

/* Class to manage Bluetooth devices and stream connections via characteristics
 */
class BluetoothManager {
  BluetoothDevice connectedDevice; // The BLE we are connected to
  bool deviceReady = false;
  bool _connecting = false;
  BluetoothCharacteristic _connectedCharacteristic; // The live characteristic
  Stream characteristicActivityStream;
  int _characteristicMTULength;
  List<BluetoothService> _services;

  HashMap<String, Function()> _activityMap;

  /* Prevent default construction
   */
  BluetoothManager._();

  /* Boot strap the class given the JSOn config.
   */
  BluetoothManager.from(Map<String, dynamic> jsonConfig) {
    _activityMap = new HashMap<String, Function()>();
    _services = [];
    return;
  }

  /* Is the given BLE device name registered as an Arduino activity device
   */
  bool deviceIsArduinoNanoActivityDevice(String deviceName) {
    return _activityMap.containsKey(deviceName);
  }

  /* Register the given device as an Arduino activity device
   */
  void registerArduinoNanoActivityDevice(
      String deviceName, Function() deviceViewBuilder) {
    if (!_activityMap.containsKey(deviceName)) {
      _activityMap[deviceName] = deviceViewBuilder;
    }
  }

  /* Get the registered function that builds the Flutter view for the given
     Arduino Nano activity device view - if device name not registered pass
     back the error view builder.
   */
  Function() getDeviceViewBuilder(Function() errorViewBuilder) {
    if (_activityMap.containsKey(connectedDevice.name)) {
      return _activityMap[connectedDevice.name];
    }
    return errorViewBuilder;
  }

  /* The BLE libraries have a default of 20 characters for the length of the
     messages sent for teh characteristic notifies. So we need to allow this to
     be extended to the max length needed for the messages sent by the
     Arduino activity devices. If a null or negative length is given we set the
     default of 20.
   */
  set characteristicMTULength(int mtuLength) {
    if (mtuLength < 1 || mtuLength == null) {
      _characteristicMTULength = 20;
    } else {
      _characteristicMTULength = mtuLength;
    }
  }

  int get characteristicMTULength {
    return _characteristicMTULength;
  }

  set services(List<BluetoothService> bleServices) {
    _services = bleServices;
  }

  /* Is BLE connection established and ready to use ?
   */
  bool get connectedAndReady {
    return connectedDevice != null && deviceReady;
  }

  /* Is the BLE device in the processes of establishing a connection.
   */
  bool get connecting {
    return _connecting;
  }

  String get deviceName {
    return connectedDevice.name.toString();
  }

  /* Iterate all services to find the service that contains the specific
     notification characteristic used to transmit the BLE message for
     the given characteristic name
  */
  void findAndSetCharacteristic(String characteristicNameToFind) {
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
              _connectedCharacteristic = characteristic;
            }
          }
        }
      }
    }
  }

  bool isCharacteristicStreamLive(String characteristicName) {
    if (connectedDevice != null && deviceReady == true) {
      if (_connectedCharacteristic != null) {
        if (_connectedCharacteristic.uuid.toString() == characteristicName) {
          if (characteristicActivityStream != null) {
            return true;
          }
        }
      }
    }
    return false;
  }

  /* Get the stream that is attached to the notifications for the given
     characteristic.
   */
  Future<Stream> getActivityStream(String characteristicName) async {
    /* Is there already a live stream for the requested characteristic UUID
     */
    if (isCharacteristicStreamLive(characteristicName)) {
      return characteristicActivityStream;
    } else {
      /* If no live stream for requested characteristic find & connect
      */
      findAndSetCharacteristic(characteristicName);
      if (_connectedCharacteristic != null && connectedDevice != null) {
        if (_connectedCharacteristic.properties.notify) {
          if (!_connectedCharacteristic.isNotifying) {
            await _connectedCharacteristic.setNotifyValue(true);
            if (_connectedCharacteristic != null) {
              characteristicActivityStream = _connectedCharacteristic.value;
              characteristicActivityStream =
                  characteristicActivityStream.asBroadcastStream();
            }
          }
        }
      }
    }
    return characteristicActivityStream;
  }

  /* Connect to the given BLE device.
   */
  Future<bool> connect(BluetoothDevice device) async {
    connectedDevice = device;
    try {
      _connecting = true;
      await connectedDevice.connect();

      /* Request the MTU of teh required size and then wait until the
         current MTU size matches the requested MTU size.
       */
      await connectedDevice.requestMtu(characteristicMTULength);
      int mtu = await device.mtu.first;
      while (mtu != characteristicMTULength) {
        print("Waiting for requested MTU");
        await Future.delayed(Duration(seconds: 1));
        mtu = await device.mtu.first;
      }
      _connecting = false;
      deviceReady = true;
    } catch (e) {
      if (e.code != 'already_connected') {
        throw e;
      }
    } finally {
      _services = await device.discoverServices();
    }
    return (deviceReady && _services != null);
  }

  /* If connected to a BLE device, disconnect
   */
  Future<bool> disconnect() async {
    if (connectedDevice != null) {
      if (_connectedCharacteristic != null) {
        try {
          await _connectedCharacteristic.setNotifyValue(false);
          _connectedCharacteristic = null;
        } catch (e) {
          print(e.toString());
        }
      }
      await connectedDevice.disconnect();
      connectedDevice = null;
      deviceReady = false;
    }
    return true;
  }
}
