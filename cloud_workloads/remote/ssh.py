import paramiko


def ssh_connect_kwargs(user, passwd=None, key_filename=None):
    """
    Builds a dictionary for sending as keyword arguments to various
    paramiko functions.

    @param user - String user name
    @param passwd - String password to use, if omitted, connections will
        attempt to use keys for authentication.
    @return - Dict

    """
    kwargs = {'look_for_keys': False, 'username': user}
    if passwd:
        kwargs.update(password=passwd)
    if key_filename:
        kwargs.update(key_filename=key_filename)
    return kwargs


def test_ssh_with_key(host, user, key_filename=None):
    """
    Tests ssh'ing into host without using a password.

    @param host - String host
    @param user - String username
    @return boolean - True for success false otherwise

    """
    exception = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = ssh_connect_kwargs(user, key_filename=key_filename)
        connect_kwargs['timeout'] = 5
        ssh.connect(host, **connect_kwargs)
        ssh.close()
        success = True
    except Exception as e:
        exception = e
        success = False

    return (success, exception)


def test_ssh_with_pass(host, user, passwd):
    """
    Tests ssh'ing into host without using a password.

    @param host - String host
    @param user - String username
    @return boolean - True for success false otherwise

    """
    exception = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = ssh_connect_kwargs(user, passwd=passwd)
        connect_kwargs['timeout'] = 5
        ssh.connect(host, **connect_kwargs)
        ssh.close()
        success = True
    except Exception as e:
        success = False
        exception = e
    return (success, exception)


def test_sftp(host, user, port=22, passwd=None, key_filename=None):
    """
    Tests whether or not we can open an sftp connection to host
    using keys(if no passwd) or password based authentication.

    @param host - String host
    @param user - String username
    @param passwd - String passwd to connect with.
    @return boolean - True for success, False otherwise.
    """
    exception = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = ssh_connect_kwargs(
            user,
            passwd=passwd,
            key_filename=key_filename
        )
        connect_kwargs['timeout'] = 5
        ssh.connect(host, **connect_kwargs)
        sftp = ssh.open_sftp()
        sftp.close()
        ssh.close()
        success = True
    except Exception as e:
        success = False
        exception = e
    return (success, exception)


def test_ssh_sudo(host, user, passwd=None, key_filename=None):
    """
    Tests whether or not we can sudo without a passwd.
    ssh's into host before running "sudo whoami"
    Checks the stdout stream. Chould contain "root".

    @param host - String host
    @param user - String user
    @param passwd - Use key for authentication if not provided
    @return boolean - True for succes false otherwise.
    """
    exception = None
    success = False
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = ssh_connect_kwargs(
            user,
            passwd=passwd,
            key_filename=key_filename
        )
        connect_kwargs['timeout'] = 5
        ssh.connect(host, **connect_kwargs)
        stdin, stdout, stderr = ssh.exec_command("sudo whoami")
        result = stdout.read().rstrip()
        ssh.close()
        if result == "root":
            success = True
        else:
            raise Exception("Unable to sudo")
    except Exception as e:
        exception = e
    return (success, exception)
