from typing import Deque
from collections import deque
import pandas as pd
from BLEMessage import BLEMessage
from BLEStream import BLEStream


class BLEFileStream(BLEStream):
    """
    Class to manage an ordered set of accelerometer updates over Bluetooth and persist them to file.
    """
    _data: Deque[BLEMessage]
    _accelerometer_data: pd.DataFrame
    _output_file: str

    def __init__(self,
                 output_file: str
                 ):
        self._data = deque()
        self._output_file = output_file
        self._accelerometer_data = None  # noqa
        self._reset()
        return

    def _reset(self):
        self._accelerometer_data = pd.DataFrame(columns=['accel_x', 'accel_y', 'accel_z'])
        return

    def open(self) -> None:
        """
        Just log the stream as active.
        """
        print("BLE File Stream ready on output file {}".format(self._output_file))
        return

    def close(self) -> None:
        """
        Write the current set of values to the output file.
        """
        print("Write data to csv {}".format(self._output_file))
        self._write_to_csv_file()
        return

    def write_value(self,
                    ble_message: BLEMessage) -> None:
        """
        Write an accelerometer into the stream BLE stream. This will have the effect of just adding the
        message to the data buffer.
        :param ble_message: The xyz accelerometer update in from of a BLEMEssage
        """
        self._data.append(ble_message)
        return

    def _write_to_csv_file(self) -> None:
        """
        Write all of the collected BLE Messages to the output file as csv
        """
        self._reset()
        for msg in self._data:
            ser = pd.Series(msg.get(), index=self._accelerometer_data.columns)
            self._accelerometer_data = self._accelerometer_data.append(ser, ignore_index=True)
        self._accelerometer_data.to_csv(self._output_file)
        return
