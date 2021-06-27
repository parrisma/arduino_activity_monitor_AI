import argparse
from os.path import isfile, exists
from os import path


class BaseArgParser:
    parser: argparse.ArgumentParser

    def __init__(self,
                 description: str):
        self._parser = argparse.ArgumentParser(description=description)
        self._parser.add_argument("-d", "--data",
                                  help="The path to the saved training data",
                                  default='./data',
                                  nargs='?',
                                  type=self.valid_path)
        self._parser.add_argument("-c", "--checkpoint",
                                  help="The path where model checkpoints will be saved",
                                  default='./checkpoint/',
                                  nargs='?',
                                  type=self.valid_path)
        self._parser.add_argument("-v", "--verbose",
                                  help="Enable verbose logging of activity",
                                  action='store_true')
        return

    def parser(self) -> argparse.ArgumentParser:
        """
        Get the base argument parser that handles all core command line options
        :return: The base argument parser.
        """
        return self._parser

    @staticmethod
    def valid_file(arg: str,
                   extension: str = None) -> str:
        """
        The given argument must be the name of a valid file and if specified must have the given file
        extension.
        :param arg: The argument to verify as an existing file.
        :param extension: An option file extension to check for e.g. csv
        :return: the argument as given as raise a value exception
        """
        if not isfile(arg):
            raise ValueError("Given file [{}] must exist".format(arg))
        if extension is not None:
            _, file_extension = path.splitext(arg)
            if file_extension != extension:
                raise ValueError("Expected file with extension [{}] but got [{}]".format(extension, file_extension))
        return arg

    @staticmethod
    def valid_path(arg: str) -> str:
        """
        The given argument must be the name of a valid path
        :param arg: The argument to verify as an existing path.
        :return: the argument as given as raise a value exception
        """
        if not exists(arg):
            raise ValueError("Given path [{}] must exist".format(arg))
        return arg
