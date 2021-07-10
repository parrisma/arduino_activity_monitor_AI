import asyncio
from bleak import BleakScanner
from bleak import BleakClient
from BLEPredictMessage import BLEPredictMessage
from Conf import Conf


class BLEActivityListener:
    """
    Class to connect to the Arduino Nano BLE device and consume activity predictions.
    """
    _ble_device_name: str  # The name as of the Arduino BLE device as set in the sketch loaded on that device
    _ble_connect_timeout: int
    _sample_period: int
    _ble_base_uuid: str  # All BLE UUID have a common base UUID
    _ble_characteristic_uuid: str  # This UUID is arbitrary and must just be the same here and in the sketch (conf.json)
    _ble_characteristic_len: int  # The number of bytes that make up the message
    _notify_uuid_prediction: str
    _verbose: bool

    # connect timeout in seconds for waiting for the BLE device to accept connection.
    _ble_connect_timeout = 20

    # The number of seconds to collect updates for.
    _sample_period = 10

    def __init__(self,
                 conf: Conf,
                 sample_period: int = 10,
                 verbose: bool = True):
        """
        Establish the BLEActivityListener
        :param conf: JSON Config manager
        :param sample_period: The number of seconds to listen for
        :param verbose: If True enable verbose logging
        """
        self._verbose = verbose
        try:
            self._ble_device_name = conf.config['ble_predictor']['service_name']
            self._ble_base_uuid = conf.config['ble_predictor']['ble_base_uuid']
            self._ble_characteristic_uuid = conf.config['ble_predictor']['characteristic_uuid']
            self._ble_characteristic_uuid = conf.config['ble_predictor']['characteristic_uuid']
            self._ble_characteristic_len = int(conf.config['ble_predictor']['characteristic_len'])
        except Exception as e:
            raise ValueError(
                "Missing or bad settings in config file [{}] with error [{}]".format(conf.source_file, str(e)))
        self._notify_uuid_prediction = self._ble_characteristic_uuid + self._ble_base_uuid.format(0XFFE1)
        self._sample_period = sample_period
        self._ble_device_address = None
        return

    def prediction_callback(self, sender, data):
        """
        Process a Notify event from the Arduino carrying a string encoded accelerometer update
        :param sender: The details of the BLE Device sending the Notify
        :param data: The data attached to the notify message
        """
        ble_msg = BLEPredictMessage(source=sender, value=data[:self._ble_characteristic_len])
        if self._verbose:
            print(str(ble_msg))
        return

    async def run(self):
        devices = await BleakScanner.discover()  # Scan for available BLE devices

        # Connect to the device 'ActivityCollector'; the exact device name is set in the JSON config.
        # The Arduino sketches use the same JSON config
        for d in devices:
            if d.name == self._ble_device_name:
                self._ble_device_address = d
                break  # we only connect to the first device with this name

        if self._ble_device_address is not None:
            async with BleakClient(self._ble_device_address, timeout=self._ble_connect_timeout) as client:

                print("connect to {} at address {}".format(self._ble_device_name, self._ble_device_address))
                try:
                    await client.start_notify(self._notify_uuid_prediction, self.prediction_callback)
                    await asyncio.sleep(self._sample_period)
                    await client.stop_notify(self._notify_uuid_prediction)
                    print("Disconnect from {} at address {}".format(self._ble_device_name, self._ble_device_address))
                    print("Done Ok")
                except Exception as e:
                    print(e)
        else:
            print("No BLE device with name {} found".format(self._ble_device_name))
