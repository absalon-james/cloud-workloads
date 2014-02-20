import cStringIO
import os
from common.workload import Workload as BaseWorkload
from common.view import View


class Iteration(dict):
    """
    Class that parses results from an iteration of dbt2 testing.
    """

    tpm_tag = " new-order transactions per minute (NOTPM)"
    duration_tag = " minute duration"
    unknown_errors_tag = " total unknown errors"
    rollback_transactions_tag = " rollback transactions"

    def __init__(self, output, previous_tpm, warehouses, host, connections):
        self.previous_tpm = previous_tpm
        self.update({
            'warehouses': warehouses,
            'host': host,
            'connections': connections,
            'tpm': None,
            'delta': None,
            'duration': None,
            'unknown_errors': None,
            'rollback_transactions': None
        })
        self._parse(output)

    def _parse(self, output):
        for line in output:
            line = line[:-1]
            if line.endswith(self.tpm_tag):
                new_tpm = float(line.split()[0])
                self['delta'] = new_tpm - self.previous_tpm
                self['tpm'] = new_tpm

            elif line.endswith(self.duration_tag):
                self['duration'] = line.split()[0]

            elif line.endswith(self.unknown_errors_tag):
                self['unknown_errors'] = line.split()[0]

            elif line.endswith(self.rollback_transactions_tag):
                self['rollback_transactions'] = line.split()[0]

    def __str__(self):
        return "\n\t".join([
            "Mysql DBT2 Result",
            "New Order Transactions per minute: %s" % self.get('tpm'),
            "Change over last: %s" % self.get('delta'),
            "Warehouses used: %s " % self.get('warehouses'),
            "Connections: %s" % self.get('connections'),
            "Duration: %s minutes" % self.get('duration'),
            "Unknown Errors: %s" % self.get('unknown_errors'),
            "Rollback Transactions: %s" % self.get('rollback_transactions')
        ])


class Workload(BaseWorkload):
    """
    Class that handles a MySQL workload.
    """

    DEFAULT_STATES = {
        'dbt2_db': ['dbt2.db'],
        'dbt2': ['dbt2.dbt2']
    }

    DEFAULT_ANTI_STATES = {
        'dbt2_db': ['dbt2.antidb'],
        'dbt2': ['dbt2.antidbt2']
    }

    DEFAULT_CONFIG = {
        'dbt2_role': 'dbt2',
        'dbt2_db_role': 'dbt2_db',
        'dbt2_path': '/opt/dbt2-0.37.50.3',

        # Should be updated via pillar
        'user': 'dbt2',
        'password': 'dbt2',
        'database': 'dbt2',
        'warehouses': 5,
        'mysql_path': '/usr/lib/mysql',

        # Should be updated via pillar or workload config
        'duration': 180,
        'connections': 20,
        'first_warehouse': 1,
        'last_warehouse': 1,
        'mindelta': 250
    }

    DEPLOY_SEQUENCE = [
        {'state': 'dbt2.db',
         'next': {'state': 'dbt2.dbt2'}},
    ]

    UNDEPLOY_SEQUENCE = [
        {'state': 'dbt2.antidb'},
        {'state': 'dbt2.antidbt2'}
    ]

    def __init__(self, client, pool, config):
        super(Workload, self).__init__(client, pool, config)
        self._results = []

    def deploy(self):
        super(Workload, self).deploy()

        # update config information from pillar
        minions = self.minions_with_role(self.config['dbt2_role'])
        pillar = self.client.get_pillar(minions, 'db', {})
        self.config.update(pillar.values()[0])
        self.config.update({'location': self.location()})

    @property
    def name(self):
        """
        Returns the name of the workload.

        :returns: String name of the workload
        """
        return "MySQL"

    def location(self):
        """
        Returns the mysql host.
        Taken from the config.

        :returns: String
        """
        minion = self.minions_with_role(self.config['dbt2_db_role'])[0]
        ips_dict = self.client.get_ips(minion, interface='private')
        return ips_dict.values()[0][0]

    def command(self, last_warehouse):
        """
        Assembles the command that would be run via the command line.
        :returns: List of arguments
        """
        cmd = ("/bin/bash %s --connections %s --time %s --warehouses %s "
               "--database %s --host %s --user %s --password %s "
               "--first-warehouse %s --last-warehouse %s --lib-client-path %s "
               "--zero-delay")

        return cmd % (
            os.path.join(self.config['dbt2_path'], 'scripts/run_mysql.sh'),
            self.config['connections'],
            self.config['duration'],
            self.config['warehouses'],
            self.config['database'],
            self.config['location'],
            self.config['user'],
            self.config['password'],
            self.config['first_warehouse'],
            last_warehouse,
            self.config['mysql_path'])

    @property
    def best_run(self):
        best_run = None
        if len(self._results) > 0:
            f = lambda it: it['tpm']
            best_run = max(self._results, key=f)
        return best_run

    def run(self):
        """Runs the workload"""

        previous_tpm = 0
        last_warehouse = int(self.config['last_warehouse'])
        total_warehouses = int(self.config['warehouses'])

        runners = self.minions_with_role(self.config['dbt2_role'])

        #devnull = open(os.devnull, 'wb')

        while (True):
            # Cannot execute command with more than the total number
            # of warehouses available.
            if last_warehouse > total_warehouses:
                break

            cmd = self.command(last_warehouse)

            kwargs = {
                'timeout': 2 * int(self.config['duration']),
                'arg': (cmd,),
            }
            exe_resp = self.client.cmd(runners[0].id_, 'cmd.run_all', **kwargs)
            exe_resp = exe_resp.values()[0]

            if exe_resp['retcode'] not in [0]:
                print exe_resp.get('stderr') or "No stderr"
                break
            stdout = cStringIO.StringIO(exe_resp['stdout'])

            result = Iteration(stdout, previous_tpm, last_warehouse,
                               self.config['location'],
                               self.config['connections'])
            self._results.append(result)

            print result
            previous_tpm = result.get('tpm')
            if result.get('delta') < int(self.config['mindelta']):
                break

            last_warehouse += 1

        print "\n\nBest run"
        print self.best_run

    @property
    def tpm_plot(self):
        return [{'x': it.get('warehouses'),
                'y': it.get('tpm')} for it in self._results]

    def view(self):
        """
        Should return a string view of this workload.  The string should be
        valid html that can be dumped with other html.

        :returns: String html representation of workload output
        """
        best_run = self.best_run

        return View('mysql.html', {
            'tpm': best_run.get('tpm'),
            'warehouses': best_run.get('warehouses'),
            'tpm_plot': self.tpm_plot
        })

if __name__ == "__main__":
    load = Workload()
    load.run()
