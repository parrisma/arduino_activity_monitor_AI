import sys
from BaseArgParser import BaseArgParser
from Conf import Conf


class MainConvertJson:
    _config_file: str

    def __init__(self):
        args = self._get_args(description="Collect and store data over Bluetooth from Arduino Nano ")
        self._config_file = args.json
        self._export_path = args.xport
        return

    @staticmethod
    def _get_args(description: str):
        """
        Extract and verify command line arguments
        :param description: The description of the application
        """
        parser = BaseArgParser(description).parser()
        parser.add_argument("-x", "--xport",
                            help="The path to export the cpp & h files to",
                            default='./conf_export',
                            nargs='?',
                            type=BaseArgParser.valid_path)
        return parser.parse_args()

    def run(self) -> None:
        conf = Conf(json_config_file=self._config_file,
                    export_path=self._export_path)
        conf.export_as_cpp()
        return


if __name__ == "__main__":
    MainConvertJson().run()
    sys.exit(0)
