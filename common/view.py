import os
from jinja2 import Environment, FileSystemLoader

VIEW_DIR = os.path.join(os.path.dirname(__file__), '../views')
JINJA_FILE_LOADER = FileSystemLoader(VIEW_DIR)
JINJA_ENV = Environment(loader=JINJA_FILE_LOADER)


class View(str):
    """
    Creates a view by rendering a jinja template.

    """
    def __new__(self, name, **kwargs):
        """
        Reads in the file at view<location>

        :param location: Location of view within the views directory
        :param mapping: Dictionary of templated parameters to be mapped
                        into the view
        """
        return JINJA_ENV.get_template(name).render(kwargs)
