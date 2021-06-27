import sys
import asyncio
from BLEActivityDataCollector import BLEActivityDataCollector
from BLEClassifierStream import BLEClassifierStream
from ActivityModel import ActivityModel
from BaseArgParser import BaseArgParser


class MainLiveActivityClassifier:
    _sample_time_in_seconds: int
    _activity_model: ActivityModel
    _script: str
    _help: str
    _verbose: bool

    def __init__(self):
        args = self._get_args(description="Classify a live stream of accelerometer readings from the Arduino")
        self._verbose = args.verbose
        self._sample_time_in_seconds = args.sample_time
        self._model_type = ActivityModel.ModelType.str2modeltype(args.model)

        self._activity_model = ActivityModel(data_file_path=args.data,
                                             checkpoint_filepath=args.checkpoint,
                                             export_filepath='',
                                             model_type=self._model_type)
        self._activity_model.load_model_from_checkpoint()
        return

    def _get_args(self,
                  description: str):
        """
        Extract and verify command line arguments
        :param description: The description of the application
        """
        parser = BaseArgParser(description).parser()
        parser.add_argument("-s", "--sample_time",
                            help="The number of seconds to sample and classify for",
                            default=60,
                            type=int)
        parser.add_argument("-m", "--model",
                            help="The type of neural network model to create",
                            choices=ActivityModel.ModelType.model_options(),  # noqa
                            default=ActivityModel.ModelType.default_model_type(),
                            type=ActivityModel.ModelType.valid_model_type)
        return parser.parse_args()

    def run(self, argv) -> None:
        self._get_args(argv)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            BLEActivityDataCollector(ble_stream=BLEClassifierStream(activity_model=self._activity_model),
                                     sample_period=self._sample_time_in_seconds,
                                     verbose=self._verbose).run())
        loop.close()
        return

    def exit_with_help(self,
                       exit_status: int = -1) -> None:
        """
        Print the help message and exit with the given exit status
        :param exit_status: exits status (-ve => error)
        """
        if exit_status < 0:
            print(self._help, file=sys.stderr)
        else:
            print(self._help)
        sys.exit(exit_status)


if __name__ == "__main__":
    MainLiveActivityClassifier().run(sys.argv[1:])
