import asyncio
from bleak import BleakScanner
from bleak import BleakClient
from BLEMessage import BLEMessage
from BLEStream import BLEStream


class BLEActivityDataCollector:
    """
    Class to connect to the Arduino Nano BLE device and consume & record accelerometer updates.
    """
    _ble_device_name: str
    _ble_connect_timeout: int
    _sample_period: int
    _ble_base_uuid: str
    _notify_uuid_accel_xyz: str
    _verbose: bool

    # The name as of the Arduino BLE device as set in the sketch loaded on that device
    _ble_device_name = "ActivityPredictor"

    # connect timeout in seconds for waiting for the BLE device to accept connection.
    _ble_connect_timeout = 20

    # The number of seconds to collect updates for.
    _sample_period = 10

    # All BLE UUID have a common base UUID
    _ble_base_uuid = "-0000-1000-8000-00805F9B34FB"

    # This UUID is set in the Arduino Sketch - it is arbitrary and must just be the same here and in the sketch
    _notify_uuid_accel_xyz = "0000f001" + _ble_base_uuid.format(0xFFE1)

    def __init__(self,
                 ble_stream: BLEStream,
                 sample_period: int = 10,
                 verbose: bool = True):
        """
        Establish the BLEActivityCollector
        :param ble_stream: The BLE Stream to send the updates to.
        """
        self._verbose = verbose
        self._sample_period = sample_period
        self._ble_device_address = None
        self._ble_stream = ble_stream
        self._ble_stream.open()
        return

    def callback_accel_xyz(self, sender, data):
        """
        Process a Notify event from the Arduino carrying a string encoded accelerometer update
        :param sender: The details of the BLE Device sending the Notify
        :param data: The data attached to the notify message
        """
        ble_msg = BLEMessage(source=sender, value=data)
        self._ble_stream.write_value(ble_msg)
        if self._verbose:
            print(str(ble_msg))
        return

    async def run(self):
        devices = await BleakScanner.discover()  # Scan for available BLE devices

        # Connect to the device with the name 'ActivityPredictor'; this is arbitrary and is set in the
        # sketch loaded on the Arduino nano. So must just match up both ends.
        for d in devices:
            if d.name == self._ble_device_name:
                self._ble_device_address = d
                break  # we only connect to teh first device with this name

        if self._ble_device_address is not None:
            async with BleakClient(self._ble_device_address, timeout=self._ble_connect_timeout) as client:

                print("connect to {} at address {}".format(self._ble_device_name, self._ble_device_address))
                try:
                    await client.start_notify(BLEActivityDataCollector._notify_uuid_accel_xyz, self.callback_accel_xyz)
                    await asyncio.sleep(self._sample_period)
                    await client.stop_notify(BLEActivityDataCollector._notify_uuid_accel_xyz)
                    print("Disconnect from {} at address {}".format(self._ble_device_name, self._ble_device_address))
                    self._ble_stream.close()
                    print("Done Ok")
                except Exception as e:
                    print(e)
        else:
            print("No BLE device with name {} found".format(self._ble_device_name))
