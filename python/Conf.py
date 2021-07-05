import json
from ConfigGenerator import ConfigGenerator


class Conf:
    _conf: object
    _source_file: str

    def __init__(self,
                 json_config_file: str) -> None:
        """
        Open and parse the JSON config file.
        :param json_config_file: The JSON config file to parse
        """
        fl = None
        try:
            fl = open(json_config_file, 'r')
            self._conf = json.load(fl)
        except Exception as e:
            raise ValueError("Cannot open JSON config file [{}]".format(str(e)))
        finally:
            if fl is not None:
                fl.close()

        self.export_as_cpp()
        return

    @property
    def config(self):
        """
        The object resulting from the parse of the JSON config file.
        :return: Dictionary of values loaded values as dictionary indexed by the JSON item names.
        """
        return self._conf

    @property
    def source_file(self) -> str:
        """
        The name of the JSON file used to boot strap the configuration
        :return: JOSN file name
        """
        return self._source_file

    def export_as_cpp(self) -> None:
        """
        Export the JSON config as a .cpp and .h file that can be pulled directly into an Arduino sketch
        where the JSON is an escaped string literal. This string can then be parsed by ArduionJson library
        this sharing the exact same configuration between the python servers and the JSON sketches

        ArduionJson: https://github.com/bblanchon/ArduinoJson
        """
        ConfigGenerator().generate_conf_files(".", json.dumps(self._conf))
        return
