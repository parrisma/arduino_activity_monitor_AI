import sys
import asyncio
from BLEActivityDataCollector import BLEActivityDataCollector
from BLEFileStream import BLEFileStream
from BaseArgParser import BaseArgParser
from Conf import Conf
from os.path import exists
from os import path


class MainDataCollect:
    _data_dir: str
    _sample_time_in_seconds: int
    _script: str
    _help: str
    _config_file: str

    def __init__(self):
        args = self._get_args(description="Collect and store data over Bluetooth from Arduino Nano ")
        self._verbose = args.verbose
        self._data_dir = args.data
        self._sample_time_in_seconds = args.sample_time
        self._activity_type = args.activity
        self._out_file = self._next_sequential_file()
        self._config_file = args.json
        return

    def _next_sequential_file(self) -> str:
        """
        All data files for teh activity type are of the form <data_path>/type-<n>.csv e.g. <data_path>/circle-1.csv.
        This function used the data path and the activity type and finds the next file in the sequence.

        :return: The full path and name of the next file in the activity sequence.
        """
        file_sequence_id = 1
        while 1:
            next_file = path.join(self._data_dir, '{}-{}.csv'.format(self._activity_type, file_sequence_id))
            if not exists(next_file):
                break
            file_sequence_id += 1
        return next_file

    @staticmethod
    def _get_args(description: str):
        """
        Extract and verify command line arguments
        :param description: The description of the application
        """
        parser = BaseArgParser(description).parser()
        parser.add_argument("-s", "--sample_time",
                            help="The number of seconds to sample and classify for",
                            default=20,
                            type=int)
        parser.add_argument("-a", "--activity",
                            help="The activity type being recorded",
                            choices=['circle', 'up-down', 'stationary-hand'])
        return parser.parse_args()

    def run(self) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(BLEActivityDataCollector(conf=Conf(self._config_file),
                                                         ble_stream=BLEFileStream(self._out_file),
                                                         sample_period=self._sample_time_in_seconds).run())
        loop.close()
        return


if __name__ == "__main__":
    MainDataCollect().run()
    sys.exit(0)
