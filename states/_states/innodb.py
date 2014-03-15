"""
Fixes innodb log file size if different than specified.
=======================================================
"""

import ConfigParser
import os


class _InnodbLogFileScanner(list):

    _sizemap = {
        'G': 1024 * 1024 * 1024,
        'M': 1024 * 1024,
        'K': 1024
    }

    _logfiles = [
        '/var/lib/mysql/ib_logfile0',
        '/var/lib/mysql/ib_logfile1'
    ]

    def __init__(self):
        super(_InnodbLogFileScanner, self).__init__()
        self.innodb_log_file_size = self._get_innodb_log_file_size()
        for file_ in self._logfiles:
            try:
                size = os.path.getsize(file_)
                if size != self.innodb_log_file_size:
                    self.append(file_)
            except:
                pass

    def _convert_to_bytes(self, sizestring):
        """
        Converts memory size indications like 256M to bytes.
        If the size indication is already in bytes, nothing
        is done.

        :param sizestring: String containing memory size indication
        :return: Integer number of bytes
        """

        for power in self._sizemap.keys():
            if power in sizestring:
                num = int(sizestring[:-1])
                return num * self._sizemap[power]

        return int(sizestring)    

    def _get_innodb_log_file_size(self):
        """
        Reads the mysql conf to get the innodb log file size.
        Returns the integer number of bytes

        :return: Integer number of bytes
        """
        myconf = ConfigParser.ConfigParser(allow_no_value=True)
        myconf.read('/etc/mysql/my.cnf')
        logfilesize = myconf.get('mysqld', 'innodb_log_file_size')
        return self._convert_to_bytes(logfilesize)

def fix_logs(name, **kwargs):

    is_test = __opts__.get('test', False)

    ret = {
        'name': name,
        'changes': {},
        'result': True,
        'comment': "Nothing happened.  Logfile sizes are correct."
    }

    try:
        changing_files = _InnodbLogFileScanner()
    except Exception, e:
        ret['result'] = None if is_test else False
        ret['comment'] = "Unable to examine mysql config and/or innodb log files."
        ret['comment'] = str(e)
        return ret

    if __salt__['service.available']('mysql') is False:
        ret['result'] = None if is_test else False
        ret['comment'] = 'Mysql service is unavailable'
        return ret

    mysql_running = __salt__['service.status']('mysql')

    if is_test:
        if len(changing_files):
            if mysql_running:
                ret['changes']['stop mysql'] = "Mysql will be stopped."

            ret['changes']['innodb logfiles'] = "Existing innodb logfiles will be removed."
            ret['changes']['start mysql'] = "Mysql will be started."
        ret['result'] = None
        return ret

    if len(changing_files):

        # Stop Mysql if it is running
        if mysql_running:
            ret['changes']['Stop Mysql'] = __salt__['service.stop']('mysql')

        # Remove innodb files if they exist
        filesremoved = []
        for file_ in changing_files._logfiles:
            if os.path.isfile(file_):
                try:
                    __salt__['file.remove'](file_)
                    filesremoved.append(file_)
                except CommandExecutionError as exc:
                    ret['result'] = False
                    ret['comment'] = '%s' % exc
                    return ret
        if len(filesremoved) > 0:
            ret['changes']['removed'] = ', '.join(filesremoved)

        # Restart Mysql
        ret['changes']['Start Mysql'] = __salt__['service.start']('mysql')

        # Make sure Mysql is running
        mysql_running = __salt__['service.status']('mysql')
        if mysql_running:
            ret['result'] = True
            ret['comment'] = "Corrected innodb log files"
        else:
            ret['result'] = False
            ret['comment'] = "Unable to restart the mysql service"

    else:
        ret['comment'] = "Innodb log file sizes are correct"
    return ret
