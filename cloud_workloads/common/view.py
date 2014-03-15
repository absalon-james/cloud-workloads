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

        @param location - Location of view within the views directory
        @param mapping - Dictionary of templated parameters to be mapped
                        into the view
        @return - Returns a string

        """
        return JINJA_ENV.get_template(name).render(kwargs)


class ExceptionView(str):
    """
    Creates a view to render an exception that has occurred while deploying
    and/or running a workload.

    """
    def __new__(self, workload, trace):
        """
        Creates a string using the jinja exception template.

        @param workload - Workload under which the exception occurred.
        @param exception - The exception that occurred.
        @param trace - Stack trace of the exception
        @return - Returns a string

        """
        return JINJA_ENV \
            .get_template('workload-exception.html') \
            .render(workload=workload, trace=trace)
