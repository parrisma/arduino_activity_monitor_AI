import sys
import getopt
import asyncio
from BLEActivityDataCollector import BLEActivityDataCollector
from BLEClassifierStream import BLEClassifierStream
from ActivityModel import ActivityModel


class MainLiveActivityClassifier:
    _sample_time_in_seconds: int
    _checkpoint_file_path: str
    _activity_model: ActivityModel
    _script: str
    _help: str
    _verbose: bool

    def __init__(self):
        self._out_file = None  # noqa
        self._verbose = False
        self._sample_time_in_seconds = 60
        self._checkpoint_file_path = './checkpoint/'
        self._activity_model = ActivityModel(checkpoint_filepath=self._checkpoint_file_path, test_on_load=False)
        self._activity_model.load_model_from_checkpoint()
        self._activity_model.export_as_tf_lite()
        self._script = 'MainLiveClassifier.py'
        self._help = '{} -v [flag verbose] -s <sample and classify period in seconds'.format(self._script)
        return

    def _get_args(self, argv) -> None:
        """
        Extract command line arguments to member variable or exit with error.
        :param argv: Command line arguments.
        """
        try:
            opts, args = getopt.getopt(argv, "hvs:", ["sample="])
        except getopt.GetoptError:
            self.exit_with_help()
        for opt, arg in opts:
            if opt == '-h':
                self.exit_with_help(2)
            if opt == '-v':
                self._verbose = True
            elif opt in ("-s", "--sample"):
                self._sample_time_in_seconds = int(arg)
        print("Ready to classify activity for a sample period of {} seconds".format(self._sample_time_in_seconds))
        return

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
