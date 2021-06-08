import numpy as np
import tensorflow as tf


class ActivityModel:
    _n_features: int
    _n_classes: int
    _look_back_window_size: int
    _activity_lstm: tf.keras.Model

    def __init__(self):
        self._n_features = 3
        self._n_classes = 3
        self._look_back_window_size = 20
        self._activity_lstm = self.create_model()
        return

    def data_to_look_back_data_set(self,
                                   three_axis_accelerometer_data,
                                   look_back_window_size) -> np.ndarray:
        """
        Take an n by 3 vector and convert to an m by look_back_window_size by 3 array. Where the window
        is slid by one position for each new row of the resulting vector.
        :param three_axis_accelerometer_data: the data set as <n> by <3 (x,y,z)> vector
        :param look_back_window_size:
        :return: Data in look back frames as numpy array
        """
        num_frames = len(three_axis_accelerometer_data) - (look_back_window_size - 1)
        look_back_data_set = np.zeros((num_frames, look_back_window_size, self._n_features))
        i = 0
        for f in range(0, num_frames):
            look_back_data_set[i] = (three_axis_accelerometer_data[i:i + look_back_window_size]).transpose()
            i += 1
        return look_back_data_set

    def create_model(self) -> tf.keras.Model:
        """
        Create the LSTM model that will be used as the sequence classifier
        """
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(input_shape=(self._look_back_window_size, self._n_features), units=1, name='Input'),
            tf.keras.layers.Dense(200, activation=tf.nn.relu, name='dense1'),
            tf.keras.layers.Dropout(rate=0.5, name="Dropout"),
            tf.keras.layers.Dense(200, activation=tf.nn.relu, name='dense2'),
            tf.keras.layers.Dense(self._n_classes, activation='softmax', name='output')
        ])
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-2),
            loss=tf.keras.losses.categorical_crossentropy
        )
        return model
