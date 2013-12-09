from common.gatling.stats import Stats
from common.gatling.workload import Workload as GatlingWorkload
from common.view import View


class Workload(GatlingWorkload):
    """
    Class that handles a magento cloud workload.
    """

    def _config(self):
        """
        Loads necessary configuration values for this workload.
        """
        super(Workload, self)._config("config/magento.ini")

    @property
    def name(self):
        """
        Returns name of the workload.

        :returns: String name of the workload
        """
        return 'Magento'

    def command(self):
        """
        Assembles the command that would be run via command line.

        :returns: String
        """
        return super(Workload, self).command('magento.CheckoutSimulation')

    def view(self):
        iteration = self.best_iteration
        stats = Stats(iteration)

        view = View('magento.html', {
            'users': iteration.users,
            'duration': iteration.duration,
            'mean_response_time': iteration.mean_response_time,
            'requests_per_second_plot': stats.requests_per_second_plot,
            'active_sessions_per_second_plot': stats.sessions_per_second_plot,
            'response_times_plot': stats.response_times_plot
        })

        return view

if __name__ == '__main__':
    Workload().run()
