"""
Collection of common console input functions.

"""


def get_input(prompt, default=""):
    """
    Prompts the user for input according to prompt. Allows the use of a
    default.

    @param prompt - String
    @param default - String
    @return string

    """
    result = raw_input(prompt)
    if not result:
        result = default
    return result


def get_yes_no(prompt, default_yes=False):
    """
    Returns true for yes, false otherwise.
    Asks the user to enter yes or no from the prompt.
    The default can be set to yes, otherwise it is no.

    @param prompt - String to display to user when asking for yes or no.
    @param default_yes - Set to true to default user's answer to yes
    @return Boolean

    """
    default = 'y' if default_yes else 'n'
    result = get_input(prompt, default)
    result = result.lower()
    if result[0] == 'y':
        return True
    return False
