from typing import List, Tuple
import numpy as np
import tensorflow as tf
import pandas as pd
import matplotlib.pyplot as plt
import re
from os import listdir
from os.path import isfile, join
from sklearn.model_selection import train_test_split


class ActivityModel:
    _n_features: int
    _n_classes: int
    _look_back_window_size: int
    _activity_lstm: tf.keras.Model
    _data_file_path: str
    _activity_classes: List[Tuple[re.Pattern, np.array]]
    _x_train: np.array
    _y_train: np.array
    _x_test: np.array
    _y_test: np.array

    _CIRCLE = 0
    _STATIONARY = 1
    _UP_DOWN = 2
    _PATTERN = 0
    _CLASS_AS_ONE_HOT = 1

    def __init__(self,
                 data_file_path: str = '\\.data'):
        self._n_features = 3
        self._n_classes = 3
        self._look_back_window_size = 20
        self._activity_lstm = self.create_model()
        self._data_file_path = data_file_path  # check path exists and that there are files
        self._activity_classes = [
            (re.compile('^circle.*\\.csv$'), np.array([1, 0, 0])),
            (re.compile('^stationary.*\\.csv$'), np.array([0, 1, 0])),
            (re.compile('^up-down.*\\.csv$'), np.array([0, 0, 1]))
        ]
        self.load_data('.\data')
        history = self._activity_lstm.fit(self._x_train, self._y_train, epochs=500, batch_size=32, verbose=2)
        plt.plot(history.history['loss'])
        plt.show()
        res = self._activity_lstm.predict(self._x_test)
        num_correct = np.sum(np.all((np.round(res, 0) == self._y_test), axis=1) * 1)
        print("Test accuracy {}".format(num_correct / np.shape(self._x_test)[0]))
        return

    def load_data(self,
                  data_file_path: str) -> None:
        """
        Load all of the data files that are of known activity class and create x_train,y_train,x_test,y_test split
        in the given ratio.
        :param data_file_path: The path where the data files are stored.
        """
        x_all = None
        y_all = None
        data_files = [f for f in listdir(data_file_path) if isfile(join(data_file_path, f))]
        for f in data_files:
            if self._activity_classes[self._CIRCLE][self._PATTERN].match(f):
                data_class_as_one_hot = self._activity_classes[self._CIRCLE][self._CLASS_AS_ONE_HOT]
            elif self._activity_classes[self._STATIONARY][self._PATTERN].match(f):
                data_class_as_one_hot = self._activity_classes[self._STATIONARY][self._CLASS_AS_ONE_HOT]
            elif self._activity_classes[self._UP_DOWN][self._PATTERN].match(f):
                data_class_as_one_hot = self._activity_classes[self._UP_DOWN][self._CLASS_AS_ONE_HOT]
            else:
                data_class_as_one_hot = None
            if data_class_as_one_hot is not None:
                print("Loading [{}]".format(f))
                # Load csv as DataFrame and remove the first index column.
                x = np.delete(pd.read_csv(join(data_file_path, f)).to_numpy(), 0, 1)
                x, y = self.data_to_look_back_data_set(x, data_class_as_one_hot)
                if x_all is None:
                    x_all = x
                    y_all = y
                else:
                    x_all = np.concatenate((x_all, x))
                    y_all = np.concatenate((y_all, y))
            else:
                print("Skipping data file [{}] as it has un known type".format(f))

        if len(x_all) > 0:
            self._x_train, self._x_test, self._y_train, self._y_test = train_test_split(x_all,
                                                                                        y_all,
                                                                                        test_size=0.2,
                                                                                        random_state=42,
                                                                                        shuffle=True)
        else:
            raise ValueError("No data to train from found in [{}]".format(data_file_path
                                                                          ))
        return

    def data_to_look_back_data_set(self,
                                   x_data: np.array,
                                   x_data_one_hot: np.array) -> Tuple[np.ndarray, np.ndarray]:
        """
        Take x and y data and convert into look_back format data suitable for LSTM training.
        :param x_data: the X data set
        :param x_data_one_hot: the one hot encoding of teh data type of X (Circle etc)
        :param look_back_window_size:
        :return: X,Y data as look back frames.
        """
        num_frames = len(x_data) - (self._look_back_window_size - 1)
        x_look_back_data_set = np.zeros((num_frames, self._look_back_window_size, x_data.shape[1]))
        y_look_back_data_set = np.zeros((num_frames, x_data_one_hot.shape[0]))
        i = 0
        for f in range(0, num_frames):
            x_look_back_data_set[i] = (x_data[i:i + self._look_back_window_size])
            y_look_back_data_set[i] = x_data_one_hot
            i += 1
        return (x_look_back_data_set, y_look_back_data_set)

    def create_model(self) -> tf.keras.Model:
        """
        Create the LSTM model that will be used as the sequence classifier
        """
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(units=50,
                                 input_shape=(self._look_back_window_size, self._n_features),
                                 return_sequences=False, name="lstm-1"),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(100, activation='relu', name="dense-1"),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(25, activation='relu', name="dense-2"),
            tf.keras.layers.Dense(self._n_classes, activation='softmax', name='output')
        ])
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss=tf.keras.losses.categorical_crossentropy
        )
        print(model.summary())
        return model


if __name__ == "__main__":
    am = ActivityModel()
    # history = am._activity_lstm.fit(x_train, y_train, epochs=500, batch_size=32, verbose=2)
    # plt.plot(history.history['loss'])
    # plt.show()
