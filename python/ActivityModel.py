from enum import IntEnum, unique, auto
from typing import List, Tuple
from copy import copy
import numpy as np
import tensorflow as tf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import rcParams
import re
import glob
from os import listdir, remove
from os.path import isfile, join
from sklearn.model_selection import train_test_split
from TFLiteGenerator import TFLiteGenerator
from Conf import Conf


class ActivityModel:
    """
    Class to manage the prediction of activity types based on Arduino Nano accelerometer readings. Where the activity
    prediction is performed by one of a selection of models.

    """

    @unique
    class ModelType(IntEnum):
        LSTM = auto()
        CNN = auto()
        SIMPLE = auto()

        @staticmethod
        def model_options() -> List[str]:
            return ['lstm', 'cnn', 'simple']

        @staticmethod
        def default_model_type() -> str:
            return ActivityModel.ModelType.model_options()[1]  # CNN is default

        @staticmethod
        def valid_model_type(arg: str) -> str:
            if arg.lower() not in ActivityModel.ModelType.model_options():
                raise ValueError("[{}] is not a valid model type".format(arg))
            return arg

        @staticmethod
        def str2modeltype(arg: str) -> 'ActivityModel.ModelType':
            if arg.lower() == ActivityModel.ModelType.model_options()[0]:
                return ActivityModel.ModelType.LSTM
            elif arg.lower() == ActivityModel.ModelType.model_options()[1]:
                return ActivityModel.ModelType.CNN
            elif arg.lower() == ActivityModel.ModelType.model_options()[2]:
                return ActivityModel.ModelType.SIMPLE
            else:
                raise ValueError("[{}] is not a valid model type".format(arg))

    _n_features: int
    _n_classes: int
    _look_back_window_size: int
    _activity_model: tf.keras.Model
    _activity_model_type: ModelType
    _activity_model_input_shape: Tuple
    _activity_model_trained: bool
    _training_steps: int
    _data_file_path: str
    _checkpoint_filepath: str
    _export_filepath: str
    _generate_tflite: bool
    _check_point_file_name_format: str
    _check_point_file_pattern: re.Pattern
    _activity_classes: List[Tuple[re.Pattern, np.array, str]]
    _x_train: np.array
    _y_train: np.array
    _x_test: np.array
    _y_test: np.array
    _test_on_load: bool

    _CIRCLE = 0
    _STATIONARY = 1
    _UP_DOWN = 2
    _PATTERN = 0
    _CLASS_AS_ONE_HOT = 1
    _ACTIVITY_NAME = 2

    def __init__(self,
                 conf: Conf,
                 data_file_path: str,
                 checkpoint_filepath: str,
                 export_filepath: str,
                 model_type: ModelType = ModelType.CNN,
                 generate_tflite: bool = False,
                 test_on_load: bool = True):
        rcParams.update({'figure.autolayout': True})  # graph plotting.
        physical_devices = tf.config.list_physical_devices('GPU')
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
        self._activity_model_type = model_type
        model_name = model_type.name.lower()
        self._n_features = conf.config[model_name]['num_features']  # x,y,z Accelerometer readings
        self._look_back_window_size = conf.config[model_name]['look_back_window_size']
        self._test_on_load = test_on_load
        self._activity_model_trained = False
        self._training_steps = conf.config[model_name]['training_steps']
        self._data_file_path = data_file_path
        self._checkpoint_filepath = checkpoint_filepath
        self._export_filepath = export_filepath
        self._generate_tflite = generate_tflite
        self._check_point_file_name_format = 'cp-' + model_name + '-{epoch:04d}.ckpt'
        self._check_point_file_pattern = re.compile('.*cp.*ckpt.*')
        self._activity_classes = list()
        for cls in conf.config['classes']:
            class_name = cls['class_name']
            one_hot = cls['one_hot']
            self._activity_classes.append(tuple((re.compile('^' + class_name + '.*\\.csv$'),
                                                 np.array(one_hot),
                                                 class_name)))
        self._n_classes = len(self._activity_classes)  # Circle, Up-Down & Stationary
        self._activity_model, self._activity_model_input_shape = self.create_model(self._activity_model_type)
        self._x_train = None
        self._x_test = None
        self._y_train = None
        self._y_test = None
        return

    def look_back_window_size(self) -> int:
        """
        Get the size of the look back window to be used by the model.

        This tells us how many sequential samples to consider when making up a training event.

        :return: The look back window size as int.
        """
        return copy(self._look_back_window_size)

    def classification_input_shape(self) -> Tuple:
        """
        The input dimensions required by the model to perform *single sample* classification.

        Because we pass a batch of inputs into the model for training we need to add the additional dimension.
        If the model shape is (20, 3, 3) and we pass in a batch Keras expects (None, 20, 3, 3) where None
        is a placeholder for a batch of unknown (at the point of model compilation) inputs. So we take the
        input shape as defined by the model, and we add the additional leading dimension of 1. Where it is 1 because
        we are passing in a single item for classification rather than a list.

        :return: Tuple of integers describing the required input shape
        """
        return tuple((1, *self._activity_model_input_shape))

    def _clean(self) -> None:
        """
        Clean up any persistent training state
        """

        # Delete any previous checkpoint files so as not to mix up results from different training runs.
        checkpoint_files = glob.glob(join(self._checkpoint_filepath, "*"))
        for f in checkpoint_files:
            if self._check_point_file_pattern.match(f):
                remove(f)

        # If generate TF Lite is enabled then delete any old generated files.
        if self._generate_tflite:
            checkpoint_files = glob.glob(join(self._export_filepath, "*"))
            for f in checkpoint_files:
                if self._check_point_file_pattern.match(f):
                    remove(f)
        return

    def train(self) -> None:
        """
        Train the model on the loaded test data.
        """
        self._clean()
        if self._x_train is not None:
            cpfp = join(self._checkpoint_filepath, self._check_point_file_name_format)
            model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
                filepath=cpfp,
                save_weights_only=True,
                monitor='val_loss',
                mode='min',  # Smallest validation loss
                save_best_only=True)

            history = self._activity_model.fit(self._x_train,
                                               self._y_train,
                                               epochs=self._training_steps,
                                               batch_size=32,
                                               verbose=2,  # Print training commentary
                                               validation_data=(self._x_test, self._y_test),
                                               callbacks=[model_checkpoint_callback])
            self._activity_model_trained = True
            self._plot_training_results(history)
            if self._generate_tflite:
                self.export_as_tf_lite()
        else:
            raise RuntimeError("Create the model and Load training data before training model")
        return

    @staticmethod
    def _plot_training_results(history: tf.keras.callbacks.History) -> None:
        """
        Plot the training and validation losses. This is done on a dual axis where the last 80% of the points
        are re-plotted so that there is the effect of a zoom as they will be on a new scale beyond (hopefully)
        the point at which the main training gains have been made.
        :param: history: The history from the Keras training.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        fig.suptitle('Training Loss & validation loss')
        fig.tight_layout()

        loss = history.history['loss']
        val_loss = history.history['val_loss']

        idx = range(len(loss))
        idx_zoom = int(len(loss) * .2)
        line1 = ax.plot(idx, loss, label='Loss', c=colors.cnames['darkblue'])
        line2 = ax.plot(idx, val_loss, label='Validation Loss', c=colors.cnames['darkorange'])
        ax2 = ax.twinx()
        line3 = ax2.plot(idx[idx_zoom:], loss[idx_zoom:], label='Loss (zoom)', c=colors.cnames['blue'])
        line4 = ax2.plot(idx[idx_zoom:], val_loss[idx_zoom:], label='Validation Loss (zoom)', c=colors.cnames['orange'])

        # added these three lines
        lines = line1 + line2 + line3 + line4
        labs = [line.get_label() for line in lines]
        ax.legend(lines, labs, loc=0)

        ax.grid()
        ax.set_xlabel('Epoch Number')
        ax.set_ylabel('Training')
        ax2.set_ylabel('Zoomed Training')

        plt.show()
        return

    def load_model_from_checkpoint(self) -> None:
        """
        Load the model weights from a saved CheckPoint or train the model from scratch
        """
        if self._activity_model is not None:
            checkpoint_to_load = tf.train.latest_checkpoint(self._checkpoint_filepath)
            print("Found [{}] to load weights from".format(checkpoint_to_load))
            self._activity_model.load_weights(checkpoint_to_load)
            if self._test_on_load and self._x_test is not None:
                loss = self._activity_model.evaluate(self._x_test, self._y_test, verbose=2)
                print("Loss of loaded checkpoint [{}]".format(loss))
            self._activity_model_trained = True
        else:
            raise RuntimeError("creat the model before loading saved model weights")
        return

    def test(self) -> None:
        """
        Test the trained model on the test data split out when the data was originally loaded.
        """
        if self._activity_model_trained:
            # Used the trained model to predict classifications based on the test data
            predictions = self._activity_model.predict(self._x_test)

            # Count how many of the predictions are equal to the expected classifications
            pred_am = np.argmax(predictions, axis=-1)
            y_test_am = np.argmax(self._y_test, axis=-1)
            num_correct = pred_am == y_test_am
            print("Test accuracy {}%".format(100 * (np.sum(num_correct) / np.shape(self._x_test)[0])))

            confusion = tf.math.confusion_matrix(
                labels=tf.constant(y_test_am),
                predictions=tf.constant(pred_am),
                num_classes=self._n_classes)

            print("Confusion Matrix \n{}".format(confusion))
        else:
            raise RuntimeError("Train the model or load weights from checkpoint before running test")
        return

    def _reshaspe(self,
                  x_all: np.ndarray) -> np.ndarray:
        """
        Take a full data set and (optionally) reshape it as needed for the model that is the target for the
        training.

        :param x_all: A fully loaded set of x values.

        :return: Reshaped set of x values in shape required by currently loaded model.
        """
        if self._activity_model_input_shape != x_all.shape[1:]:
            x_all = x_all.reshape(tuple((x_all.shape[0], *self._activity_model_input_shape)))
        return x_all

    def load_training_data(self) -> None:
        """
        Load all the data files that are of known activity class and create x_train,y_train,x_test,y_test split
        in the given ratio. By default, the data is split into frames that are the size of the defined look back
        window.

        Then once the data is loaded it is reshaped (if needed) to match the specific input shape of the target
        model.
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
                print("Warning, Skipping data file [{}] as it has un known type".format(f))

        # Ensure the X data is in the correct shape as required by the current target model.
        x_all = self._reshaspe(x_all=x_all)

        if len(x_all) > 0:
            self._x_train, self._x_test, self._y_train, self._y_test = train_test_split(x_all,
                                                                                        y_all,
                                                                                        test_size=0.2,
                                                                                        random_state=42,
                                                                                        shuffle=True)
        else:
            raise ValueError("No data to train from found in [{}]".format(self._data_file_path))
        return

    def predict(self,
                sample_window: np.ndarray) -> Tuple[float, str]:
        """
        Make a model prediction based on the single sample given, where the sample
        id a numpy array of features with shape (1, look back window size, num features)
        :param sample_window: The numpy array containing the sample window
        :return: The sample confidence as 0.0 to 1.0 and the string name of the predicted activity.
        """
        prediction = self._activity_model.predict(sample_window)
        certainty = np.max(prediction) * 100
        activity = np.round(prediction, 0)
        activity_name = "Unknown"
        for cl in self._activity_classes:
            if np.all(cl[self._CLASS_AS_ONE_HOT] == activity[0]):
                activity_name = cl[self._ACTIVITY_NAME]
                break
        return (certainty, activity_name)  # noqa

    def run_experiment(self,
                       experiment_file: str = './experiment-1.csv') -> None:
        """
        Load the experiment file and predict the sequence of activity it collected. Do this by selecting 10%
        of random entry points and 'look_back_window' slice of observations.
        """
        print("Loading experiment[{}]".format(experiment_file))
        # Load csv as DataFrame and remove the first index column.
        x = np.delete(pd.read_csv(experiment_file).to_numpy(), 0, 1)
        x, _ = self.data_to_look_back_data_set(x, np.zeros((1)))
        shape = (1, x.shape[1], x.shape[2], 1)
        # for i in np.random.randint(0, x.shape[0], int(x.shape[0] * .1)):  # Run 10% as tests
        for i in range(x.shape[0]):
            certainty, activity_name = self.predict(np.reshape(x[i], shape))
            print("Sample # [{}] Activity [{}] with certainty {:.0f}%".format(i, activity_name, certainty))
        return

    def data_to_look_back_data_set(self,
                                   x_data: np.array,
                                   x_data_one_hot: np.array) -> Tuple[np.ndarray, np.ndarray]:
        """
        Take x and y data and convert into look_back format data suitable for LSTM training.
        :param x_data: the X data set
        :param x_data_one_hot: the one hot encoding of the data type of X (Circle etc.)
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
        return tuple((x_look_back_data_set, y_look_back_data_set))

    def create_model(self,
                     model_type: 'ModelType') -> Tuple[tf.keras.Model, Tuple]:
        """
        Create a model of the given type
        """
        if model_type == self.ModelType.LSTM:
            model, shape = self.create_lstm_network()
        elif model_type == self.ModelType.SIMPLE:
            model, shape = self.create_simple_network()
        else:
            model, shape = self.create_cnn_network()
        return tuple((model, shape))

    def create_cnn_network(self) -> Tuple[tf.keras.Model, Tuple]:
        """
        Create the CNN model that will be used as the accelerometer sequence classifier.

        This is a 1D Convolution, but modelled as a 2D Conv as the target TF Lite environment does
        not (yet) support 1D Convolution
        """
        shape = tuple((self._look_back_window_size, self._n_features, 1))
        model = tf.keras.Sequential([
            tf.keras.layers.Conv2D(filters=8, kernel_size=(3, 1), activation='relu',
                                   input_shape=shape, name='Conv2D-1'),
            tf.keras.layers.Conv2D(filters=4, kernel_size=(3, 1), activation='relu', name='Conv2D-2'),
            tf.keras.layers.Dropout(0.5, name="Dropout-Regularise1"),
            tf.keras.layers.MaxPooling2D(pool_size=(2, 1), name='MaxPool1'),
            tf.keras.layers.Dropout(0.4, name="Dropout-Regularise2"),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(25, activation='relu', name='Dense1'),
            tf.keras.layers.Dropout(0.3, name="Dropout-Regularise3"),
            tf.keras.layers.Dense(self._n_classes, activation='softmax', name='Output')
        ], name="cnn-activity-model")

        #
        # Compile model using Adam optimiser and Categorical Cross Entropy as this is a classification model.
        #
        decayed_lr = tf.keras.optimizers.schedules.ExponentialDecay(initial_learning_rate=1e-3,
                                                                    decay_steps=10000,
                                                                    decay_rate=0.95,
                                                                    staircase=True)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=decayed_lr),
            loss=tf.keras.losses.categorical_crossentropy
        )
        print(model.summary())
        return tuple((model, shape))

    def create_lstm_network(self) -> Tuple[tf.keras.Model, Tuple]:
        """
        Create the LSTM model that will be used as the accelerometer sequence classifier
        """
        shape = tuple((self._look_back_window_size, self._n_features))
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(units=10,
                                 input_shape=shape,
                                 return_sequences=False, name="lstm-1"),
            tf.keras.layers.Dropout(0.2, name="Dropout-Regularise1"),
            tf.keras.layers.Dense(50, activation='relu', name="dense-1"),
            tf.keras.layers.Dropout(0.2, name="Dropout-Regularise2"),
            tf.keras.layers.Dense(10, activation='relu', name="dense-2"),
            tf.keras.layers.Dense(self._n_classes, activation='softmax', name='output')
        ], name="lstm-activity-model")

        #
        # Compile model using Adam optimiser and Categorical Cross Entropy as this is a classification model.
        #
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss=tf.keras.losses.categorical_crossentropy
        )
        print(model.summary())
        return tuple((model, shape))

    def create_simple_network(self) -> Tuple[tf.keras.Model, Tuple]:
        """
        Treat the sequence as a flat vector of length look_back * num_features
        :return: A Dense model.
        """
        shape = self._look_back_window_size * self._n_features
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(units=shape,
                                  input_dim=1,
                                  activation='relu',
                                  name="input"),
            tf.keras.layers.Dense(units=round(self._look_back_window_size / self._n_features, 0),
                                  activation='relu',
                                  name="dense-1"),
            tf.keras.layers.Dropout(0.3, name="Dropout-Regularise1"),
            tf.keras.layers.Dense(units=self._n_features * 2,
                                  activation='relu',
                                  name="dense-2"),
            tf.keras.layers.Dense(self._n_classes, activation='softmax', name='output')
        ], name="simple-model")

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss=tf.keras.losses.categorical_crossentropy
        )

        print(model.summary())
        return tuple((model, tuple(shape)))

    def export_as_tf_lite(self) -> None:
        """
        Convert the loaded & trained model to a tensorflow lite form and also create the c file
        equivalent that can be uploaded to the Arduino Nano 33 SENSE to be run using the Arduino
        tf lite sketch libraries.

        The binary form is written as <model_name>.tfl
        The c form is written as <model_name>.h

        Both of these are written to the export file path defined in this class.
        """
        if self._activity_model is not None and self._activity_model_trained:
            TFLiteGenerator.generate_tflite_files(file_path=self._export_filepath,
                                                  model_to_export=self._activity_model)
        else:
            raise ValueError("The model must be both created and trained before it can be exported as TF-Lite")
        return
