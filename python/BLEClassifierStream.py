import numpy as np
from typing import Deque
from collections import deque
from BLEMessage import BLEMessage
from BLEStream import BLEStream
from ActivityModel import ActivityModel


class BLEClassifierStream(BLEStream):
    """
    Class to classify a rolling window of accelerometer updates
    """
    _data: Deque[BLEMessage]
    _classifier_window_len: int
    _output_file: str
    _activity_model: ActivityModel

    def __init__(self,
                 activity_model: ActivityModel
                 ):
        self._activity_model = activity_model
        self._classifier_window_len = self._activity_model.look_back_window_size()
        self._data = deque(maxlen=self._classifier_window_len)  # we only keep a rolling window as needed by the model.
        self._accelerometer_data = None  # noqa
        return

    def open(self) -> None:
        """
        Just log the stream as active.
        """
        print("BLE Classifier Stream ready")
        return

    def close(self) -> None:
        """
        Just not the stream as finished
        """
        print("BLE Classifier Stream finished")
        return

    def _as_numpy(self) -> np.ndarray:
        """
        Covert the current data to numpy form needed to pass to model for classification.
        :return: numpy array of dimension [1, len data, 3]
        """
        asnp = np.zeros(self._activity_model.classification_input_shape())
        for i in range(0, len(self._data)):
            asnp[0, i] = np.asarray(self._data[i].get())
            i += 1
        return asnp

    def write_value(self,
                    ble_message: BLEMessage) -> None:
        """
        Track tle last window_len of accelerometer updates and as soon as there are sufficient messages
        start classifying the activity.
        :param ble_message: The xyz accelerometer update in from of a BLEMEssage
        """
        self._data.append(ble_message)
        if len(self._data) >= self._classifier_window_len:
            certainty, activity_name = self._activity_model.predict(self._as_numpy())
            print("{}: Activity [{}] with certainty {:.0f}%".format(self.ts(),
                                                                    activity_name,
                                                                    certainty))
        else:
            print("{}: Waiting for sufficient data {} of required {} seen ".format(self.ts(),
                                                                                   len(self._data),
                                                                                   self._classifier_window_len))
        return
