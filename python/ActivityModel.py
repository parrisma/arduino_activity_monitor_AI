from typing import List, Tuple
import numpy as np
import tensorflow as tf
import pandas as pd
import matplotlib.pyplot as plt
import re
import glob
from os import listdir, remove
from os.path import isfile, join, exists
from sklearn.model_selection import train_test_split


class ActivityModel:
    _n_features: int
    _n_classes: int
    _look_back_window_size: int
    _activity_lstm: tf.keras.Model
    _activity_lstm_trained: bool
    _training_steps: int
    _data_file_path: str
    _checkpoint_filepath: str
    _check_point_file_name_format: str
    _check_point_file_pattern: re.Pattern
    _activity_classes: List[Tuple[re.Pattern, np.array, str]]
    _x_train: np.array
    _y_train: np.array
    _x_test: np.array
    _y_test: np.array

    _CIRCLE = 0
    _STATIONARY = 1
    _UP_DOWN = 2
    _PATTERN = 0
    _CLASS_AS_ONE_HOT = 1
    _ACTIVTY_NAME = 2

    def __init__(self,
                 data_file_path: str = "./data",
                 checkpoint_filepath='./checkpoint/'):
        self._n_features = 3
        self._n_classes = 3
        self._look_back_window_size = 20
        self._activity_lstm = self.create_model()
        self._activity_lstm_trained = False
        self._training_steps = 500
        self._data_file_path = self._valid_path(data_file_path)
        self._checkpoint_filepath = self._valid_path(checkpoint_filepath)
        self._check_point_file_name_format = 'cp-{epoch:04d}.ckpt'
        self._check_point_file_pattern = re.compile('.*cp.*ckpt.*')
        self._activity_classes = [
            (re.compile('^circle.*\\.csv$'), np.array([1, 0, 0]), "Circle"),
            (re.compile('^stationary.*\\.csv$'), np.array([0, 1, 0]), "Stationary"),
            (re.compile('^up-down.*\\.csv$'), np.array([0, 0, 1]), "Up Down")
        ]
        self._x_train = None
        self._x_test = None
        self._y_train = None
        self._y_test = None
        return

    @staticmethod
    def _valid_path(path_to_check: str) -> str:
        """
        Return the given file path if it exists else raise a Value error
        :param path_to_check: The Path to validate as existing
        :return: The given path if it exists
        """
        if not exists(path_to_check):
            raise ValueError("Path [{}] does not exist, existing & valid path expected".format(path_to_check))
        return path_to_check

    def _clean(self) -> None:
        """
        Clean up any persistent training state
        """

        # Delete any previous checkpoint files.
        checkpoint_files = glob.glob(join(self._checkpoint_filepath, "*"))
        for f in checkpoint_files:
            if self._check_point_file_pattern.match(f):
                remove(f)
        return

    def train(self) -> None:
        """
        Train the model on the loaed test data
        """
        self._clean()
        if self._x_train is not None:
            cpfp = join(self._checkpoint_filepath, 'cp-{epoch:04d}.ckpt')
            model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
                filepath=cpfp,
                save_weights_only=True,
                monitor='val_loss',
                mode='min',  # Smallest validation loss
                save_best_only=True)

            history = self._activity_lstm.fit(self._x_train,
                                              self._y_train,
                                              epochs=self._training_steps,
                                              batch_size=32,
                                              verbose=2,  # Print training commentary
                                              validation_data=(self._x_test, self._y_test),
                                              callbacks=[model_checkpoint_callback])
            self._activity_lstm_trained = True
            plt.plot(history.history['loss'])
            plt.plot(history.history['val_loss'])
            plt.show()
        else:
            print("Create the model and Load training data before training model")
        return

    def load_from_checkpoint(self) -> None:
        """
        Load the model weights from a saved CheckPoint or train the model from scratch
        """
        if self._activity_lstm is not None and self._x_train is not None:
            checkpoint_to_load = tf.train.latest_checkpoint(self._checkpoint_filepath)
            print("Found [{}] to load weights from".format(checkpoint_to_load))
            self._activity_lstm.load_weights(checkpoint_to_load)
            loss = self._activity_lstm.evaluate(self._x_test, self._y_test, verbose=2)
            print("Loss of loaded checkpoint [{}]".format(loss))
            self._activity_lstm_trained = True
        else:
            print("creat the model and load the test data before loading a saved model weights")
        return

    def test(self) -> None:
        """
        Test the trained model on teh test data split out when the data was originally loaded.
        """
        if self._activity_lstm_trained:
            # Used the trained model to predict classifications based on the test data
            predictions = self._activity_lstm.predict(self._x_test)
            # Count how many of the predictions are equal to the expected classifications
            num_correct = np.sum(np.all((np.round(predictions, 0) == self._y_test), axis=1) * 1)

            print("Test accuracy {}%".format(100 * (num_correct / np.shape(self._x_test)[0])))
        else:
            print("Train the model before running test")
        return

    def load_data(self) -> None:
        """
        Load all of the data files that are of known activity class and create x_train,y_train,x_test,y_test split
        in the given ratio.
        """
        x_all = None
        y_all = None
        data_files = [f for f in listdir(self._data_file_path) if isfile(join(self._data_file_path, f))]
        for f in data_files:
            data_class_as_one_hot = None
            for cl in self._activity_classes:
                if cl[self._PATTERN].match(f):
                    data_class_as_one_hot = cl[self._CLASS_AS_ONE_HOT]
                    break

            if data_class_as_one_hot is not None:
                print("Loading [{}]".format(f))
                # Load csv as DataFrame and remove the first index column.
                x = np.delete(pd.read_csv(join(self._data_file_path, f)).to_numpy(), 0, 1)
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
            raise ValueError("No data to train from found in [{}]".format(self._data_file_path))
        return

    def experiment(self,
                   experiment_file: str = './experiment-1.csv') -> None:
        """
        Load the experiment file and predict the sequence of activity it collected
        """
        print("Loading experiment[{}]".format(experiment_file))
        # Load csv as DataFrame and remove the first index column.
        x = np.delete(pd.read_csv(experiment_file).to_numpy(), 0, 1)
        x, _ = self.data_to_look_back_data_set(x, np.zeros((1)))
        shape = (1, x.shape[1], x.shape[2])
        for i in range(x.shape[0]):
            prediction = self._activity_lstm.predict(np.reshape(x[i], shape))
            certainty = np.max(prediction) * 100
            activity = np.round(prediction, 0)
            activity_name = "Unknown"
            for cl in self._activity_classes:
                if np.all(cl[self._CLASS_AS_ONE_HOT] == activity[0]):
                    activity_name = cl[self._ACTIVTY_NAME]
                    break
            print("Activity [{}] with certainty {:.0f}%".format(activity_name, certainty))
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
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(100, activation='relu', name="dense-1"),
            tf.keras.layers.Dropout(0.3),
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
    am.load_data()
    am.load_from_checkpoint()
    # am.train()
    am.test()
    am.experiment('.\\data\\up-down-1.csv')
    am.experiment('.\\data\\circle-1.csv')
    am.experiment('.\\data\\stationary-hand-1.csv')
    am.experiment()
