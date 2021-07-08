import sys
import asyncio
from BLEActivityDataCollector import BLEActivityDataCollector
from BLEClassifierStream import BLEClassifierStream
from ActivityModel import ActivityModel
from BaseArgParser import BaseArgParser
from Conf import Conf


class MainLiveActivityClassifier:
    _sample_time_in_seconds: int
    _activity_model: ActivityModel
    _script: str
    _help: str
    _verbose: bool
    _config_file: str
    _conf: Conf

    def __init__(self):
        args = self._get_args(description="Classify a live stream of accelerometer readings from the Arduino")
        self._config_file = args.json
        self._conf = Conf(self._config_file)
        self._verbose = args.verbose
        self._sample_time_in_seconds = args.sample_time
        self._model_type = ActivityModel.ModelType.str2modeltype(args.model)

        self._activity_model = ActivityModel(conf=self._conf,
                                             data_file_path=args.data,
                                             checkpoint_filepath=args.checkpoint,
                                             export_filepath='',
                                             model_type=self._model_type)
        self._activity_model.load_model_from_checkpoint()
        return

    @staticmethod
    def _get_args(description: str):
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
        parser.add_argument("-c", "--checkpoint",
                            help="The path where model checkpoints will be saved",
                            default='./checkpoint/',
                            nargs='?',
                            type=BaseArgParser.valid_path)
        return parser.parse_args()

    def run(self) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            BLEActivityDataCollector(conf=self._conf,
                                     ble_stream=BLEClassifierStream(activity_model=self._activity_model),
                                     sample_period=self._sample_time_in_seconds,
                                     verbose=self._verbose).run())
        loop.close()
        return


if __name__ == "__main__":
    MainLiveActivityClassifier().run()
    sys.exit(0)
