"""
This module contains various patches designed as cheap workarounds
until a better solution is found/released.
"""

import salt.config


def patch_default_config():
    """
    Patches bug in salt 2014.1.1 See:
        https://github.com/saltstack/salt/issues/11525
    for details.

    """
    salt.config.VALID_OPTS['ssh_passwd'] = str
    salt.config.VALID_OPTS['ssh_port'] = str
    salt.config.VALID_OPTS['ssh_sudo'] = bool
    salt.config.VALID_OPTS['ssh_timeout'] = float
    salt.config.VALID_OPTS['ssh_user'] = str

    salt.config.DEFAULT_MASTER_OPTS['ssh_passwd'] = ''
    salt.config.DEFAULT_MASTER_OPTS['ssh_port'] = '22'
    salt.config.DEFAULT_MASTER_OPTS['ssh_sudo'] = False
    salt.config.DEFAULT_MASTER_OPTS['ssh_timeout'] = 60
    salt.config.DEFAULT_MASTER_OPTS['ssh_user'] = 'root'

# Execute patches
patch_default_config()
