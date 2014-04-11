from cloud_workloads.common.gatling.workload import Workload as GatlingWorkload


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
        'duration': '90',
        'users_start': '30',
        'users_step': '30'
    }

    DEPLOY_SEQUENCE = [
        {'state': 'magento.db_master',
         'next': {'state': 'magento.db_slave'}},
        {'state': 'magento.web'},
        {'state': 'magento.gatling'}
    ]

    UNDEPLOY_SEQUENCE = [
        {'state': 'magento.antidb_master'},
        {'state': 'magento.antidb_slave'},
        {'state': 'magento.antiweb'},
        {'state': 'magento.antigatling'}
    ]

    MINION_GRAPH_EDGE_MAP = {
        'magento_gatling': ['magento_web'],
        'magento_web': ['magento_mysql_master', 'magento_mysql_slave'],
        'magento_mysql_slave': ['magento_mysql_master']
    }

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

    def data(self):
        """
        Returns an html formatted string/view for this workload.

        @return - String
        """
        if not self.data_dict.get('exception_trace'):
            run = self.best_run
            active_sessions_plot = run['stats'].sessions_per_second_plot
            self.data_dict.update({
                'users': run.users,
                'duration': run.duration,
                'mean_response_time': run.mean_response_time,
                'requests_per_second_plot':
                run['stats'].requests_per_second_plot,
                'active_sessions_per_second_plot': active_sessions_plot,
                'response_times_plot': run['stats'].response_times_plot
            })
        return self.data_dict
