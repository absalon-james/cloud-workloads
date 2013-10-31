import string

class View(str):
    """
    Creates a view by reading in a view file and mapping in content
    using python string templating.
    """
    def __new__(self, location, mapping=None):
        """
        Reads in the file at view<location>

        :param location: Location of view within the views directory
        :param mapping: Dictionary of templated parameters to be mapped
                        into the view
        """
        with open('views/%s' % location) as view_file:
            contents = view_file.read()

        if mapping:
            contents = string.Template(contents).substitute(mapping)
        return contents
