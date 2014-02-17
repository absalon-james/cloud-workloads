from common.gatling.stats import Stats
from common.gatling.workload import Workload as GatlingWorkload
from common.view import View


class Workload(GatlingWorkload):
    """
    Class that handles a magento cloud workload.
    """

    DEFAULT_STATES = {
        'magento_mysql_master': ['magento.db_master'],
        'magento_mysql_slave': ['magento.db_slave'],
        'magento_web': ['magento.web'],
        'magento_gatling': ['magento.gatling']
    }

    DEFAULT_ANTI_STATES = {
        'magento_mysql_master': ['magento.antidb_master'],
        'magento_mysql_slave': ['magento.antidb_slave'],
        'magento_web': ['magento.antiweb'],
        'magento_gatling': ['magento.antigatling']
    }

    DEFAULT_CONFIG = {
        'gatling_dir': 'gatling',
        'webhead_url': 'http://%s/magento',
        'webhead_role': 'magento_web',
        'gatling_role': 'magento_gatling',
        'gatling_user': 'gatling',
        'duration': '20',
        'users_start': '20',
        'users_step': '25'
    }

    DEPLOY_SEQUENCE = [
        {
         'state': 'magento.db_master',
         'next': {
            'state': 'magento.db_slave'
            }
        },
        {'state': 'magento.web'},
        {'state': 'magento.gatling'}
    ]

    UNDEPLOY_SEQUENCE = [
        {'state': 'magento.antidb_master'},
        {'state': 'magento.antidb_slave'},
        {'state': 'magento.antiweb'},
        {'state': 'magento.antigatling'}
    ]


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
        run = self.best_run

        view = View('magento.html', {
            'users': run.users,
            'duration': run.duration,
            'mean_response_time': run.mean_response_time,
            'requests_per_second_plot': run['stats'].requests_per_second_plot,
            'active_sessions_per_second_plot': run['stats'].sessions_per_second_plot,
            'response_times_plot': run['stats'].response_times_plot
        })

        return view

if __name__ == '__main__':
    Workload().run()
