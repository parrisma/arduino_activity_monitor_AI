from os import remove
from os.path import join, exists


class ConfigGenerator:
    GUARD_PREF: str = 'ACTIVITY_'

    @staticmethod
    def generate_conf_files(file_path: str,
                            conf_as_str: str) -> None:
        """
        Generate and save both the .h and .cpp file that are needed to import the JSON config
        :param file_path: An existing path where the files are to be generated.
        :param conf_as_str: the JSON config rendered as string
        """

        # Model name will be used to be the cpp vra name and the file names so we need no spaces.
        conf_name = 'json_conf'

        h_file_name = conf_name + '.h'
        cpp_file_name = conf_name + '.cpp'

        # Escape the string
        conf_as_escaped_str = conf_as_str.replace('"', '\\"')

        # Generate .h and .cpp from the given JSON as string
        h_as_str = ConfigGenerator._generate_h_file(conf_name=conf_name)

        cpp_as_str = ConfigGenerator._generate_cpp_file(header_file_name=h_file_name,
                                                        conf_name=conf_name,
                                                        conf_as_escaped_str=conf_as_escaped_str)

        # Write out the .h and the .cpp
        files_to_save = [[join(file_path, h_file_name), h_as_str],
                         [join(file_path, cpp_file_name), cpp_as_str]
                         ]
        for fl, file_as_str in files_to_save:
            if exists(fl):
                remove(fl)
            f = open(fl, 'w')
            f.write(file_as_str)
            f.close()

        return

    @staticmethod
    def _generate_h_file(conf_name: str) -> str:
        """
        Generate the .h header file that will be used to import the JSON config as string literal
        :param conf_name: the name of the model to use as the cpp environment variable
        """
        h_str = ''

        # Start Header guard
        h_str += '#ifndef ' + ConfigGenerator.GUARD_PREF + conf_name.upper() + '_H_\n'
        h_str += '#define ' + ConfigGenerator.GUARD_PREF + conf_name.upper() + '_H_\n\n'

        # External refs to var declared fully in teh cpp file.
        h_str += "extern const char {}[];\n".format(conf_name)
        h_str += "extern const int {}_len;\n\n".format(conf_name)

        # End Header Guard
        # Close out header guard
        h_str += '#endif //' + ConfigGenerator.GUARD_PREF + conf_name.upper() + '_H_\n'

        return h_str

    @staticmethod
    def _generate_cpp_file(header_file_name: str,
                           conf_name: str,
                           conf_as_escaped_str: str) -> str:
        """
        Convert escaped JSON config as string to a cpp variable and length
        :param header_file_name: the name of the associated header file.
        :param conf_name: the name of the model to use as the cpp environment variable
        :param conf_as_escaped_str: The config as string literal with double-quotes escaped
        """
        cpp_str = ''

        cpp_str += '#include "{}"\n'.format(header_file_name)

        # Add array length at top of file
        cpp_str += 'const int {}_len = {};\n'.format(conf_name, str(len(conf_as_escaped_str)))

        # Declare C variable
        cpp_str += 'const char ' + conf_name + '[] = '

        # Add config as escaped string literal
        cpp_str += '\"{}\"'.format(conf_as_escaped_str)

        # Add closing brace
        cpp_str += ';\n\n'

        return cpp_str
