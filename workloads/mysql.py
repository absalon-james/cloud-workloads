#import ConfigParser
import cStringIO
import os
import subprocess
import common.config_parser as ConfigParser

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
            "Mysql DBT2 Iteration",
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

    def __init__(self, config_mode="flat_file"):
        self.config_mode = config_mode
        self._iterations = []
        self._config()

    def _config(self):
        """
        Should load any necessary configuration for the workload.
        Possibilities include webheads, db server addresses, number of
        clients, etc.
        """
        self._conf = {}

        parser = ConfigParser.ConfigParser(self.config_mode)

        parser.add_section('host')
        parser.set('host', 'host', '127.0.0.1')
        parser.set('host', 'database', 'dbt2')
        parser.set('host', 'user', 'dbt2')
        parser.set('host', 'password', 'dbt2')

        parser.add_section('dbt2')
        parser.set('dbt2', 'connections', '20')
        parser.set('dbt2', 'duration', '60')
        parser.set('dbt2', 'warehouses', '10')
        parser.set('dbt2', 'firstwarehouse', '1')
        parser.set('dbt2', 'path', '/home/<user name>/dbt2-0.37.50.3/')
        parser.set('dbt2', 'mindelta', '250')

        parser.add_section('mysql-client')
        parser.set('mysql-client', 'path', '/usr/lib/mysql')

        parser.read('config/mysql.ini')

        self._conf.update({
            'host': parser.get('host', 'host'),
            'database': parser.get('host', 'database'),
            'user': parser.get('host', 'user'),
            'password': parser.get('host', 'password'),
            'connections': parser.get('dbt2', 'connections'),
            'duration': parser.get('dbt2', 'duration'),
            'warehouses': parser.get('dbt2', 'warehouses'),
            'firstwarehouse': parser.get('dbt2', 'firstwarehouse'),
            'mindelta': parser.get('dbt2', 'mindelta'),
            'dbt2_path': parser.get('dbt2', 'path'),
            'mysql_path': parser.get('mysql-client', 'path')})

    @property
    def name(self):
        """
        Returns the name of the workload.

        :returns: String name of the workload
        """
        return "MySQL"

    @property
    def host(self):
        """
        Returns the mysql host.
        Taken from the config.

        :returns: String
        """
        return self._conf.get('host')

    @property
    def database(self):
        """
        Returns the database which houses dbt2 test data.
        Taken from the config.

        :returns: String
        """
        return self._conf.get('database')

    @property
    def user(self):
        """
        Returns the user allowed to access the database.
        Taken from the config.

        :returns: String
        """
        return self._conf.get('user')

    @property
    def password(self):
        """
        Returns the password of the user allowed to access the database.
        Taken from the config.

        :returns: String
        """
        return self._conf.get('password')

    @property
    def connections(self):
        """
        Returns the number of simultaneous connections dbt2 is to use while
        benchmarking.
        Taken from the config.

        :returns: Integer
        """
        return int(self._conf.get('connections'))

    @property
    def duration(self):
        """
        Returns the duration of the test in seconds.
        Taken from the config.

        :returns: Integer
        """
        return int(self._conf.get('duration'))

    @property
    def warehouses(self):
        """
        Returns the total number of warehouses data was generated for.
        Taken from the config.

        :returns: Integer
        """
        return int(self._conf.get('warehouses'))

    @property
    def start_warehouse(self):
        """
        Returns the starting warehouse.  The first iteration will start
        at this warehouse.
        Taken from the config.

        :returns: Integer
        """
        return int(self._conf.get('firstwarehouse'))

    @property
    def mindelta(self):
        """
        Returns the minimum change that must occur from iteration to
        iteration in order to continue.

        :returns: Integer
        """
        return int(self._conf.get('mindelta'))

    @property
    def dbt2_path(self):
        """
        Returns the location of dbt2.
        Taken from the config.

        :returns: String
        """
        return self._conf.get('dbt2_path')

    @property
    def mysql_client_path(self):
        """
        Returns the location of the mysql client.  Dbt2 uses this to
        communicate with the mysql host.
        Taken from the config.

        :returns: String
        """
        return self._conf.get('mysql_path')

    def command(self, warehouses=0):
        """
        Assembles the command that would be run via the command line.
        :returns: List of arguments
        """
        return [
            '/bin/bash',  os.path.join(self.dbt2_path, 'scripts/run_mysql.sh'),
            '--connections', str(self.connections),
            '--time', str(self.duration),
            '--warehouses', str(self.warehouses),
            '--database', self.database,
            '--host', self.host,
            '--user', self.user,
            '--password', self.password,
            '--first-warehouse', str(self.start_warehouse),
            '--last-warehouse', str(warehouses),
            '--lib-client-path', self.mysql_client_path,
            '--zero-delay']

    @property
    def best_iteration(self):
        max_tpm = 0
        max_iteration = None
        for it in self._iterations:
            if it.get('tpm') > max_tpm:
                max_tpm = it.get('tpm')
                max_iteration = it

        return max_iteration

    def run(self):
        """Runs the workload"""

        previous_tpm = 0
        warehouses = self.start_warehouse
        devnull = open(os.devnull, 'wb')

        while (True):
            # Cannot execute command with more than the total number
            # of warehouses available.
            if warehouses > self.warehouses:
                break

            # Rung the command
            args = self.command(warehouses=warehouses)
            process = subprocess.Popen(args,
                                       stdout=subprocess.PIPE,
                                       stderr=devnull)
            output, err = process.communicate()

            # Only the listed return codes indicate success
            if process.returncode not in [0]:
                break

            # Parse outout into a usuable form
            output = cStringIO.StringIO(output)
            iteration = Iteration(output, previous_tpm, warehouses,
                                  self.host, self.connections)

            self._iterations.append(iteration)
            print iteration

            previous_tpm = iteration.get('tpm')
            if iteration.get('delta') < self.mindelta:
                break

            warehouses += 1

        print "\n\nBest iteration"
        print self.best_iteration

    @property
    def tpm_plot(self):
        return [{'x': it.get('warehouses'),
                'y': it.get('tpm')} for it in self._iterations]

    def view(self):
        """
        Should return a string view of this workload.  The string should be
        valid html that can be dumped with other html.

        :returns: String html representation of workload output
        """
        best_iteration = self.best_iteration
        tpm_plot = self.tpm_plot

        return View('mysql.html', {
            'tpm': best_iteration.get('tpm'),
            'warehouses': best_iteration.get('warehouses'),
            'tpm_plot': self.tpm_plot
        })

if __name__ == "__main__":
    load = Workload()
    load.run()
