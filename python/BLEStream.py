from typing import Callable
from collections import deque
import pandas as pd
from BLEMessage import BLEMessage


class BLEStream:
    """
    Class to manage an ordered set of accelerometer updates over Bluetooth and persist them to file.
    """
    _data: deque
    _message_processor_callback: Callable[[BLEMessage], None]
    _accelerometer_data: pd.DataFrame

    def __init__(self,
                 message_processor_callback: Callable[[BLEMessage], None]):
        self._data = deque()
        self._message_processor_callback = message_processor_callback
        self._accelerometer_data = None  # noqa
        self._reset()
        return

    def _reset(self):
        self._accelerometer_data = pd.DataFrame(columns=['accel_x', 'accel_y', 'accel_z'])
        return

    def process_complete_message(self,
                                 msg: BLEMessage) -> None:
        """
        Handler message called for each accelerometer update
        :param msg: The accelerometer update as BLEMessage
        """
        if self._message_processor_callback is not None:
            self._message_processor_callback(msg)
        return

    def set_value(self,
                  setter: Callable[[BLEMessage, str], None],
                  value: str) -> None:
        """
        Accept an accelerometer update, add it to the list and call notify.
        :param setter: The BLE method to update the new BLE Message that is created
        :param value: The xyz accelerometer update encoded as string as expected by the setter method
        """
        if isinstance(value, bytearray):
            value = value.decode("utf-8")
        elif isinstance(value, str):
            pass
        else:
            raise ValueError("BLEStream set_value expected type of string but got: {}".format(type(value)))
        msg = BLEMessage()
        setter(msg, value)
        self._data.append(msg)
        self._message_processor_callback(msg)
        return

    def set_accelerometer_xyz(self,
                              value) -> None:
        """
        Add the given accelerometer update to the ordered list of updates.
        :param value: The xyz update value encoded as string (See BLEMessage)
        """
        self.set_value(BLEMessage.set_accelerometer_xyz,  # noqa
                       value)
        return

    def write_to_csv_file(self,
                          filename: str) -> None:
        """
        Write all of the collected data to a csv file
        :param filename: The name of the file to write to.
        """
        self._reset()
        for msg in self._data:
            ser = pd.Series(msg.get(), index=self._accelerometer_data.columns)
            self._accelerometer_data = self._accelerometer_data.append(ser, ignore_index=True)
        self._accelerometer_data.to_csv(filename)
        return
