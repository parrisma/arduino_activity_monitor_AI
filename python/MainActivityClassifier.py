import sys
import getopt
from ActivityModel import ActivityModel
from os.path import isfile, exists


class MainActivityClassifier:
    _experiment_file: str
    _data_file_path: str
    _checkpoint_file_path: str
    _use_saved_weights: bool
    _script: str
    _help: str

    def __init__(self):
        self._experiment_file = None  # noqa
        self._data_file_path: str = "./data"
        self._checkpoint_file_path = './checkpoint/'
        self._use_saved_weights = False
        self._script = 'MainActivityClassifier.py'
        self._help = '{} \
        -h [flag: show command line help] \
        -d <path for csv training data> \
        -e <name of experiment csv file> \
        -c <model check point path> \
        -l [flag: load saved model weights]'.format(self._script)
        return

    def _get_args(self, argv) -> None:
        """
        Extract command line arguments to member variable or exit with error.
        :param argv: Command line arguments.
        """
        try:
            opts, args = getopt.getopt(argv, "hle:d:c:", ["data=", "experiment=", "checkpoint="])
        except getopt.GetoptError:
            self.exit_with_help()
        for opt, arg in opts:
            if opt == '-h':
                self.exit_with_help(2)
            if opt == '-l':
                self._use_saved_weights = True
            elif opt in ("-d", "--data"):
                if exists(arg):
                    self._data_file_path = arg
                else:
                    raise ValueError("Path for training data files must exists, but given [{}]".format(arg))
            elif opt in ("-c", "--checkpoint"):
                if exists(arg):
                    self._checkpoint_file_path = arg
                else:
                    raise ValueError("Path for model checkpoints files must exists, but given [{}]".format(arg))
            elif opt in ("-e", "--experiment"):
                if isfile(arg):
                    self._experiment_file = arg
                else:
                    raise ValueError("Experiment file must exist but given [{}]".format(arg))
        return

    def run(self, argv) -> None:

        self._get_args(argv)

        am = ActivityModel(data_file_path=self._data_file_path,
                           checkpoint_filepath=self._checkpoint_file_path)
        am.load_data()
        if self._use_saved_weights:
            am.load_from_checkpoint()
        else:
            am.train()
        am.test()
        if self._experiment_file is not None:
            am.experiment()
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
    MainActivityClassifier().run(sys.argv[1:])
