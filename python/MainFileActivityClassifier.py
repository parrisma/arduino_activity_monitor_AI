import sys
from ActivityModel import ActivityModel
from BaseArgParser import BaseArgParser


class MainFileActivityClassifier:
    _experiment_file: str
    _data_file_path: str
    _checkpoint_file_path: str
    _export_file_path: str
    _generate_tflite_files: bool
    _use_saved_weights: bool
    _model_type: ActivityModel.ModelType
    _verbose: bool

    def __init__(self):
        args = self._get_args(description="Train activity classifier based on saved training data")
        self._verbose = args.verbose
        self._experiment_file = args.experiment
        self._data_file_path = args.data
        self._checkpoint_file_path = args.checkpoint
        self._use_saved_weights = args.load_weights
        self._export_file_path = args.generate
        self._generate_tflite_files = args.tflite
        self._model_type = ActivityModel.ModelType.str2modeltype(args.model)
        return

    @staticmethod
    def _get_args(description: str):
        """
        Extract and verify command line arguments
        :param description: The description of the application
        """
        parser = BaseArgParser(description).parser()
        parser.add_argument("-l", "--load_weights",
                            help="Load saved weights from the checkpoint directory",
                            action='store_true')
        parser.add_argument("-e", "--experiment",
                            help="An existing csv file containing accelerometer data to classify",
                            type=BaseArgParser.valid_file)
        parser.add_argument("-m", "--model",
                            help="The type of neural network model to create",
                            choices=ActivityModel.ModelType.model_options(),  # noqa
                            default=ActivityModel.ModelType.default_model_type(),
                            type=ActivityModel.ModelType.valid_model_type)
        parser.add_argument("-g", "--generate",
                            help="The path where the .cpp/.h files are generated for TFlite",
                            default='./model-export/',
                            nargs='?',
                            type=BaseArgParser.valid_path)
        parser.add_argument("-t", "--tflite",
                            help="Generate the .cpp & .h mode network files for use with TFLite",
                            action='store_true')
        parser.add_argument("-c", "--checkpoint",
                            help="The path where model checkpoints will be saved",
                            default='./checkpoint/',
                            nargs='?',
                            type=BaseArgParser.valid_path)
        return parser.parse_args()

    def run(self) -> None:
        activity_model = ActivityModel(data_file_path=self._data_file_path,
                                       checkpoint_filepath=self._checkpoint_file_path,
                                       export_filepath=self._export_file_path,
                                       generate_tflite=self._generate_tflite_files,
                                       model_type=self._model_type)

        activity_model.load_training_data()

        # Either load a trained model from saved checkpoint or run a full training from the loaded data.
        # If Generate TF Lite flag has been set the TF Lite /cpp & .h files will be generated.
        if self._use_saved_weights:
            activity_model.load_model_from_checkpoint()
        else:
            activity_model.train()

        # Run model tests using the test data split out from the loaded training data.
        activity_model.test()

        # If an experiment file has been specified run predictions based on the aceeleromter data inteh
        # experiment file.
        if self._experiment_file is not None:
            activity_model.run_experiment()
        return


if __name__ == "__main__":
    MainFileActivityClassifier().run()
    sys.exit(0)
