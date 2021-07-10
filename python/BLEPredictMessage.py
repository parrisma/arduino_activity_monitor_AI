class BLEPredictMessage:
    """
    Class to manage a single activity prediction. Where the prediction is passed as a string
    """
    _source: int
    _prediction: str

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
        self._set_prediction(value)
        return

    def get_prediction(self) -> str:
        return self._prediction

    def _set_prediction(self, value) -> None:
        """
        Decode the given bytearray or string encoded update and set the string prediction
        :param value: The encoded message body as bytearray / string
        """
        if isinstance(value, bytearray):
            prediction_as_str = value.decode("utf-8")
        elif isinstance(value, str):
            prediction_as_str = value
        else:
            raise ValueError("BLEStream set_value expected type of string but got: {}".format(type(value)))

        if prediction_as_str is None or len(prediction_as_str) == 0:
            raise ValueError("BLE Message was none or empty")

        self._prediction = prediction_as_str
        return

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return "Prediction {} : {}".format(self._source, self._prediction)
