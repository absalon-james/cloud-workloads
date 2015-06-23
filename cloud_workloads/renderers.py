from common.view import ExceptionView, View
from meta import version


class HtmlRenderer(str):
    """
    Renders an html document from a list of completed workloads.

    """

    def __new__(self, workloads):
        """
        Returns a string that is the rendered html document.

        @return - String
        """

        # Primitive view is special
        primitives = None

        # Names and views of non primitive workloads
        other_names = []
        other_views = []

        for workload in workloads:
            view_data = workload.data()

            # Check to see if an exception view needs to be rendered
            trace = view_data.get('exception_trace')
            if trace:
                view = ExceptionView(workload, trace)
            else:
                view = View(workload.name.lower() + '.html', **view_data)

            if workload.is_primitive:
                primitives = view

            else:
                other_names.append(workload.name)
                other_views.append(view)

        # Render the entire view
        return View(
            'main.html',
            version=version,
            primitives=primitives,
            workloads=zip(other_names, other_views)
        )
