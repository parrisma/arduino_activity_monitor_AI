"""
Shawn Hymel
Source: https://gist.github.com/ShawnHymel/79237fe6aee5a3653c497d879f746c0c

Note: Generator modified to align with TF Lite samples supplied by Google TensorFlow team
    : as part of Arduino_TensorFlow_Lite libraries.
    :
    : Also .h and .cpp split out as separate generated code.
"""


def hex_to_c_array(hex_data,
                   var_name):
    """
    Convert raw hex data to an array format that can be written out to a c .h file.
    :param hex_data: The raw hex data as byte array
    :param var_name: The name of the array variable that will be declared for teh array in the c header file.
    :return: The c array equivalent of the raw hex in a form to write out as a c header file.
    """
    c_str = ''

    # Create header guard
    c_str += '#ifndef ' + var_name.upper() + '_H\n'
    c_str += '#define ' + var_name.upper() + '_H\n\n'

    # Add array length at top of file
    c_str += '\nunsigned int ' + var_name + '_len = ' + str(len(hex_data)) + ';\n'

    # Declare C variable
    c_str += 'alignas(8) const unsigned char ' + var_name + '[] = {'
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
    c_str += '\n ' + format(' '.join(hex_array)) + '\n};\n\n'

    # Close out header guard
    c_str += '#endif //' + var_name.upper() + '_H'

    return c_str
