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

    def set_accelerometer_x(self, x: float) -> None:
        self._accelerometer_x = x

    def set_accelerometer_y(self, y: float) -> None:
        self._accelerometer_y = y

    def set_accelerometer_z(self, z: float) -> None:
        self._accelerometer_z = z

    def complete(self) -> bool:
        return self._accelerometer_x is not None and \
               self._accelerometer_y is not None and \
               self._accelerometer_z is not None

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
                  setter: Callable[[BLEMessage, float], None],
                  getter: Callable[[BLEMessage], float],
                  value: Union[float, bytearray]) -> None:
        if isinstance(value, bytearray):
            value = struct.unpack('f', value)[0]
        elif isinstance(value, float):
            pass
        else:
            raise ValueError("BLEStream set_value expected type of bytearray or float but got: {}".format(type(value)))

        done = False
        for msg in self._stack:
            if getter(msg) is None:
                setter(msg, value)
                done = True
                if msg.complete():
                    self._message_processor_callback(msg)
                    self._stack.remove(msg)
                break
        if not done:
            new_msg = BLEMessage()
            setter(new_msg, value)
            self._stack.append(new_msg)
        return

    def set_accelerometer_x(self,
                            value) -> None:
        self.set_value(BLEMessage.set_accelerometer_x,  # noqa
                       BLEMessage.get_accelerometer_x,
                       value)
        return

    def set_accelerometer_y(self,
                            value) -> None:
        self.set_value(BLEMessage.set_accelerometer_y,  # noqa
                       BLEMessage.get_accelerometer_y,
                       value)
        return

    def set_accelerometer_z(self,
                            value) -> None:
        self.set_value(BLEMessage.set_accelerometer_z,  # noqa
                       BLEMessage.get_accelerometer_z,
                       value)
        return


class ActivityPredictor:
    ble_base_uuid = "-0000-1000-8000-00805F9B34FB"
    notify_uuid_accel_x = "0000f001" + ble_base_uuid.format(0xFFE1)
    notify_uuid_accel_y = "0000f002" + ble_base_uuid.format(0xFFE1)
    notify_uuid_accel_z = "0000f003" + ble_base_uuid.format(0xFFE1)

    def __init__(self):
        self.ble_device_address = None
        self.ble_stream = BLEStream(message_processor_callback=self.msg_handler)
        return

    def msg_handler(self,
                    msg: BLEMessage) -> None:
        print(str(msg))
        return

    def callback_accel_x(self, sender, data):
        self.ble_stream.set_accelerometer_x(data)
        return

    def callback_accel_y(self, sender, data):
        self.ble_stream.set_accelerometer_y(data)
        return

    def callback_accel_z(self, sender, data):
        self.ble_stream.set_accelerometer_z(data)
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
                    await client.start_notify(ActivityPredictor.notify_uuid_accel_x, self.callback_accel_x)
                    await client.start_notify(ActivityPredictor.notify_uuid_accel_y, self.callback_accel_y)
                    await client.start_notify(ActivityPredictor.notify_uuid_accel_z, self.callback_accel_z)
                    await asyncio.sleep(5.0)
                    await client.stop_notify(ActivityPredictor.notify_uuid_accel_x)
                except Exception as e:
                    print(e)

            print("disconnect from", self.ble_device_address)


loop = asyncio.get_event_loop()
loop.run_until_complete(ActivityPredictor().run())
loop.close()
