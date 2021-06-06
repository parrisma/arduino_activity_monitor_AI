from typing import Callable, Union
import asyncio
import struct
from bleak import BleakScanner
from bleak import BleakClient
from collections import deque


class BLEMessage:
    _accelerometer_x: float
    _accelerometer_y: float
    _accelerometer_z: float

    def __init__(self):
        self._accelerometer_x = None  # noqa
        self._accelerometer_y = None  # noqa
        self._accelerometer_z = None  # noqa
        return

    def get_accelerometer_x(self) -> float:
        return self._accelerometer_x

    def get_accelerometer_y(self) -> float:
        return self._accelerometer_y

    def get_accelerometer_z(self) -> float:
        return self._accelerometer_z

    def set_accelerometer_xyz(self, xyz_as_str: str) -> None:
        xyz = xyz_as_str.split(';')
        if len(xyz) != 3:
            raise ValueError("Expected acceleromiter xyz as ; separated string, but got [{}]".format(xyz_as_str))
        x, y, z = xyz
        self._accelerometer_x = float(x)
        self._accelerometer_y = float(y)
        self._accelerometer_z = float(z)

    def __str__(self):
        return "x: {:.3f} y: {:.3f} z: {:.3f}".format(self._accelerometer_x,
                                                      self._accelerometer_y,
                                                      self._accelerometer_z)


class BLEStream:
    _stack: deque
    _message_processor_callback: Callable[[BLEMessage], None]

    def __init__(self,
                 message_processor_callback: Callable[[BLEMessage], None]):
        self._stack = deque()
        self._message_processor_callback = message_processor_callback
        return

    @staticmethod
    def process_complete_message(self, msg: BLEMessage) -> None:
        self._message_processor_callback(msg)
        return

    def set_value(self,
                  setter: Callable[[BLEMessage, str], None],
                  value: str) -> None:
        if isinstance(value, bytearray):
            value = value.decode("utf-8")
        elif isinstance(value, str):
            pass
        else:
            raise ValueError("BLEStream set_value expected type of string but got: {}".format(type(value)))
        msg = BLEMessage()
        setter(msg, value)
        self._stack.append(msg)
        self._message_processor_callback(msg)
        return

    def set_accelerometer_xyz(self,
                              value) -> None:
        self.set_value(BLEMessage.set_accelerometer_xyz,  # noqa
                       value)
        return


class ActivityPredictor:
    ble_base_uuid = "-0000-1000-8000-00805F9B34FB"
    notify_uuid_accel_xyz = "0000f001" + ble_base_uuid.format(0xFFE1)

    def __init__(self):
        self.ble_device_address = None
        self.ble_stream = BLEStream(message_processor_callback=self.msg_handler)
        return

    def msg_handler(self,
                    msg: BLEMessage) -> None:
        print(str(msg))
        return

    def callback_accel_xyz(self, sender, data):
        self.ble_stream.set_accelerometer_xyz(data)
        return

    async def run(self):
        devices = await BleakScanner.discover()
        for d in devices:
            if d.name == "ActivityPredictor":
                self.ble_device_address = d

        if self.ble_device_address is not None:
            async with BleakClient(self.ble_device_address, timeout=5.0) as client:

                print("connect to", self.ble_device_address)
                try:
                    await client.start_notify(ActivityPredictor.notify_uuid_accel_xyz, self.callback_accel_xyz)
                    await asyncio.sleep(5.0)
                    await client.stop_notify(ActivityPredictor.notify_uuid_accel_xyz)
                except Exception as e:
                    print(e)

            print("disconnect from", self.ble_device_address)


loop = asyncio.get_event_loop()
loop.run_until_complete(ActivityPredictor().run())
loop.close()
