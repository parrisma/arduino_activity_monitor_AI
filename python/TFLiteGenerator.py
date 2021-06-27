from os import remove
from os.path import join, exists
import tensorflow as tf


class TFLiteGenerator:
    GUARD_PREF: str = 'ACTIVITY_PREDICTOR_'
    OPTIMIZE: bool = False

    @staticmethod
    def generate_tflite_files(file_path: str,
                              model_to_export: tf.keras.Model) -> None:
        """
        Generate and save both the .h and .cpp file that are needed to import the model in exported form
        on the TF Lite interpreter running on the micro controller.
        :param file_path: An existing path where the files are to be generated.
        :param model_to_export: the built, complied and trained model to export in TF Lite form
        """

        # Model name will be used to be the cpp vra name and the file names so we need no spaces.
        model_name = 'activity_model'

        h_file_name = model_name + '.h'
        cpp_file_name = model_name + '.cpp'

        # Convert teh model to binary form.
        hex_data = TFLiteGenerator._model_binary_form(model=model_to_export)

        # Generate .h and .cpp based on the generated binary form and the model name
        h_as_str = TFLiteGenerator._generate_h_file(model_name=model_name)
        cpp_as_str = TFLiteGenerator._generate_cpp_file(header_file_name=h_file_name,
                                                        model_name=model_name,
                                                        hex_data=hex_data)

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
    def _model_binary_form(model: tf.keras.Model):
        """
        Convert the given built, compiled and trained model to TF Lite binary form
        :param model: The model to convert
        :return: the model in tf lite binary form
        """
        conv = tf.lite.TFLiteConverter.from_keras_model(model)
        if TFLiteGenerator.OPTIMIZE:
            # It is possible to optimize the converted network for size. However depending on the chosen
            # network architecture that can require additional tuning to the optimization process. For
            # the networks in this example and the space capabilities of the Nano 33 Sense optimization
            # is not essential. See below for additional help on optimization.
            # https://www.tensorflow.org/lite/microcontrollers/get_started_low_level#train_a_model
            # https://www.tensorflow.org/lite/performance/post_training_quantization
            conv.optimizations = [tf.lite.Optimize.OPTIMIZE_FOR_SIZE]  # reduces size of converted form.
        return conv.convert()

    @staticmethod
    def _generate_h_file(model_name: str) -> str:
        """
        Generate the .h header file that will be used to import the model in TF Lite format on the
        Micro Controller.
        :param file_name: the name of the file to save the header file in.
        :param model_name: the name of the model to use as the cpp environment variable
        """
        h_str = ''

        # Start Header guard
        h_str += '#ifndef ' + TFLiteGenerator.GUARD_PREF + model_name.upper() + '_H_\n'
        h_str += '#define ' + TFLiteGenerator.GUARD_PREF + model_name.upper() + '_H_\n\n'

        # External refs to var declared fully in teh cpp file.
        h_str += "extern const unsigned char {}[];\n".format(model_name)
        h_str += "extern const int {}_len;\n\n".format(model_name)

        # End Header Guard
        # Close out header guard
        h_str += '#endif //' + TFLiteGenerator.GUARD_PREF + model_name.upper() + '_H_\n'

        return h_str

    @staticmethod
    def _generate_cpp_file(header_file_name: str,
                           model_name: str,
                           hex_data) -> str:
        """
        Convert raw hex data to an array format that is then written out as a .cpp file to the given file name.
        :param header_file_name: the name of the associated header file.
        :param model_name: the name of the model to use as the cpp environment variable
        :param hex_data: The raw hex data as byte array
        """
        cpp_str = ''

        cpp_str += '#include "{}"\n'.format(header_file_name)

        # Add array length at top of file
        cpp_str += 'const int {}_len = {};\n'.format(model_name, str(len(hex_data)))

        # Declare C variable
        cpp_str += 'alignas(8) const unsigned char ' + model_name + '[] = {'
        hex_array = []
        for i, val in enumerate(hex_data):

            # Construct string from hex
            hex_str = format(val, '#04x')

            # Add formatting so each line stays within 80 characters
            if (i + 1) < len(hex_data):
                hex_str += ','
            if (i + 1) % 12 == 0:
                hex_str += '\n '
            hex_array.append(hex_str)

        # Add closing brace
        cpp_str += '\n ' + format(' '.join(hex_array)) + '\n};\n\n'

        return cpp_str
