import sys
import getopt
import asyncio
from BLEActivityDataCollector import BLEActivityDataCollector
from BLEFileStream import BLEFileStream


class MainDataCollect:
    _out_file: str
    _sample_time_in_seconds: int
    _script: str
    _help: str

    def __init__(self):
        self._out_file = None  # noqa
        self._sample_time_in_seconds = 10
        self._script = 'MainDataCollect.py'
        self._help = '{} -o <output_file> -s <sample period in seconds'.format(self._script)
        return

    def _get_args(self, argv) -> None:
        """
        Extract command line arguments to member variable or exit with error.
        :param argv: Command line arguments.
        """
        try:
            opts, args = getopt.getopt(argv, "hs:o:", ["out=", "sample="])
        except getopt.GetoptError:
            self.exit_with_help()
        for opt, arg in opts:
            if opt == '-h':
                self.exit_with_help(2)
            elif opt in ("-o", "--out"):
                self._out_file = arg
            elif opt in ("-s", "--sample"):
                self._sample_time_in_seconds = int(arg)
        if self._out_file is None:
            self.exit_with_help()
        print("Output file is {} with a sample period of {} seconds".format(self._out_file,
                                                                            self._sample_time_in_seconds))
        return

    def run(self, argv) -> None:
        self._get_args(argv)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(BLEActivityDataCollector(ble_stream=BLEFileStream(self._out_file),
                                                         sample_period=self._sample_time_in_seconds).run())
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
    MainDataCollect().run(sys.argv[1:])
