from typing import List


class BLEMessage:
    """
    Class to manage a single 3 axis accelerometer update
    """
    _source: int
    _accelerometer_x: float
    _accelerometer_y: float
    _accelerometer_z: float

    def __init__(self,
                 source: int,
                 value):
        """
        Construct the BLE message based on the given message value.
        :param source: The Id / handle of the BLE source that originated this message. As there can be > 1 source
                       active at a single time.
        :param value: The encoded message as bytearray / string of the form <x as float>;<y as float>;<z as float>
        """
        self._source = source
        self._set_accelerometer_xyz(value)
        return

    def get_accelerometer_x(self) -> float:
        return self._accelerometer_x

    def get_accelerometer_y(self) -> float:
        return self._accelerometer_y

    def get_accelerometer_z(self) -> float:
        return self._accelerometer_z

    def get(self) -> List[float]:
        return [self._accelerometer_x, self._accelerometer_y, self._accelerometer_z]

    def _set_accelerometer_xyz(self, value) -> None:
        """
        Decode the given bytearray or string encoded update and set the x,y,z values
        :param value: The encoded message body as bytearray / string of the form <x as float>;<y as float>;<z as float>
        """
        if isinstance(value, bytearray):
            xyz_as_str = value.decode("utf-8")
        elif isinstance(value, str):
            xyz_as_str = value
        else:
            raise ValueError("BLEStream set_value expected type of string but got: {}".format(type(value)))

        if xyz_as_str is None or len(xyz_as_str) == 0:
            raise ValueError("BLE Message was none or empty")

        xyz = xyz_as_str.split(';')
        if len(xyz) != 4:
            raise ValueError("Expected accelerometer xyz as ; separated string, but got [{}]".format(xyz_as_str))
        x, y, z, _ = xyz
        self._accelerometer_x = float(x)
        self._accelerometer_y = float(y)
        self._accelerometer_z = float(z)
        return

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return "Source {} : x: {:.6f} y: {:.6f} z: {:.6f}".format(self._source,
                                                                  self._accelerometer_x,
                                                                  self._accelerometer_y,
                                                                  self._accelerometer_z)
