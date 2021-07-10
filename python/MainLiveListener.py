import sys
import asyncio
from BaseArgParser import BaseArgParser
from Conf import Conf
from BLEActivityListener import BLEActivityListener


class MainLiveListener:
    _sample_time_in_seconds: int
    _config_file: str

    def __init__(self):
        args = self._get_args(description="Collect and store accelerometer data over Bluetooth from Arduino Nano ")
        self._sample_time_in_seconds = args.sample_time
        self._config_file = args.json
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
                            default=20,
                            type=int)
        return parser.parse_args()

    def run(self) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(BLEActivityListener(conf=Conf(self._config_file),
                                                    sample_period=self._sample_time_in_seconds).run())
        loop.close()
        return


if __name__ == "__main__":
    MainLiveListener().run()
    sys.exit(0)
