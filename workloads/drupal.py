from common.gatling.workload import Workload as GatlingWorkload
from common.view import View


class Workload(GatlingWorkload):
    """
    Class that handles a drupal cloud workload.
    """

    DEFAULT_STATES = {
        'drupal_mysql_master': ['drupal.db_master'],
        'drupal_mysql_slave': ['drupal.db_slave'],
        'drupal_web': ['drupal.web'],
        'drupal_gatling': ['drupal.gatling']
    }

    DEFAULT_ANTI_STATES = {
        'drupal_mysql_master': ['drupal.antidb_master'],
        'drupal_mysql_slave': ['drupal.antidb_slave'],
        'drupal_web': ['drupal.antiweb'],
        'drupal_gatling': ['drupal.antigatling']
    }

    DEFAULT_CONFIG = {
        'gatling_dir': 'gatling',
        'webhead_url': 'http://%s',
        'webhead_role': 'drupal_web',
        'gatling_role': 'drupal_gatling',
        'gatling_user': 'gatling',
        'duration': '20',
        'users_start': '20',
        'users_step': '25'
    }

    DEPLOY_SEQUENCE = [
        {'state': 'drupal.db_master',
         'next': {'state': 'drupal.db_slave'}},
        {'state': 'drupal.web'},
        {'state': 'drupal.gatling'}
    ]

    UNDEPLOY_SEQUENCE = [
        {'state': 'drupal.antidb_master'},
        {'state': 'drupal.antidb_slave'},
        {'state': 'drupal.antiweb'},
        {'state': 'drupal.antigatling'}
    ]

    @property
    def name(self):
        """
        Returns name of the workload.

        :returns: String name of the workload
        """
        return 'Drupal'

    def command(self):
        """
        Assembles the command that would be run via command line.

        :returns: String
        """
        return super(Workload, self).command('drupal.UserSimulation')

    def view(self):
        run = self.best_run
        active_sessions_plot = run['stats'].sessions_per_second_plot
        self.view_dict.update({
            'users': run.users,
            'duration': run.duration,
            'mean_response_time': run.mean_response_time,
            'requests_per_second_plot': run['stats'].requests_per_second_plot,
            'active_sessions_per_second_plot': active_sessions_plot,
            'response_times_plot': run['stats'].response_times_plot
        })
        return View('drupal.html', **(self.view_dict))

if __name__ == '__main__':
    Workload().run()
