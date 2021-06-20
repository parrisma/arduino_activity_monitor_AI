from abc import ABC, abstractmethod
from BLEMessage import BLEMessage


class BLEStream(ABC):
    """
    Handle messages received from an Arduino Nano 33 Sense Blue Tooth Low energy board.
    """

    @abstractmethod
    def open(self) -> None:
        """
        Perform tasks at the point the stream is created
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Perform tasks at the point the stream is closed
        """
        pass

    @abstractmethod
    def write_value(self,
                    ble_message: BLEMessage) -> None:
        """
        Write an accelerometer into the stream BLE Messages buffer.
        :param ble_message: The xyz accelerometer update in from of a BLEMEssage
        """
        pass
