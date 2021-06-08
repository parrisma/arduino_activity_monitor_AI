from typing import List


class BLEMessage:
    """
    Class to manage a single 3 axis accelerometer update
    """
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

    def get(self) -> List[float]:
        return [self._accelerometer_x, self._accelerometer_y, self._accelerometer_z]

    def set_accelerometer_xyz(self, xyz_as_str: str) -> None:
        """
        Decode the given string encoded update and set the x,y,z values
        :param xyz_as_str: The encoded update as string of teh form <x as float>;<y as float>;<z as float>
        """
        xyz = xyz_as_str.split(';')
        if len(xyz) != 3:
            raise ValueError("Expected accelerometer xyz as ; separated string, but got [{}]".format(xyz_as_str))
        x, y, z = xyz
        self._accelerometer_x = float(x)
        self._accelerometer_y = float(y)
        self._accelerometer_z = float(z)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return "x: {:.3f} y: {:.3f} z: {:.3f}".format(self._accelerometer_x,
                                                      self._accelerometer_y,
                                                      self._accelerometer_z)
