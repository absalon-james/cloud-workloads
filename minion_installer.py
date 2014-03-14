import argparse
import netifaces
import os
import paramiko
import pprint
import salt
import salt.crypt
import salt.client
import salt.client.ssh
import salt.roster
import sys
import shutil


MASTER_CONFIG_PATH = os.environ.get('SALT_MASTER_CONFIG', '/etc/salt/master')
MASTER_OPTIONS = salt.config.master_config(MASTER_CONFIG_PATH)


def get_master_ip(interface):
    """
    Returns the ip address of the specified interface on this machine.

    @param interface - String eth0, eth1, etc.
    @return - String ip address

    """
    ifaddresses = netifaces.ifaddresses(interface)
    inet = ifaddresses[netifaces.AF_INET][0]
    return inet['addr']


class Installer(object):

    def __init__(self, master_interface='eth0'):
        """
        Object constructor

        @param master_interface - The interface of the master to pull the
            ip address from
        """
        self.master_interface = master_interface
        self.master_ip = get_master_ip(self.master_interface)

        self.roster = salt.roster.Roster(MASTER_OPTIONS).targets('*', 'glob')
        print "Type of roster", type(self.roster)
        pprint.pprint(self.roster)

    def install(self):
        """
        Installs salt-minion on all minions available to salt-ssh

        """
        # Get all minions
        self.minions = self.get_minions()

        # Update minions with hostnames
        self.get_hostnames()

        # Run the salt bootstrap script on all minions
        self.bootstrap_minions()

        # Set the master for all minions
        self.set_master()

        # Generate keys for all minions
        self.gen_keys()

        # Restart the salt minion service
        self.restart_minion_service()

    def _options(self, arg_str, expr_form='glob', target='*'):
        """
        Creates the option dictionary that is sent to salt.client.ssh.SSH
        when creating a new salt.client.ssh.SSH object

        @param arg_str - String as it would appear on the command line
        @param expr_form - How to target salt-ssh minions
        @param target - String target
        @return - Dictionary

        """
        options = {}
        options.update(MASTER_OPTIONS)
        options.update({
            'selected_target_option': expr_form,
            'tgt': target,
            'arg_str': arg_str
        })
        return options

    def _client(self, options):
        """
        Creates a salt.client.ssh.SSH object with the options provided.

        @param options - Dictionary
        @return - salt.client.ssh.SSH object

        """
        return salt.client.ssh.SSH(options)

    def _execute(self, client):
        """
        Instructs the ssh client to run and compiles the returns into
        a dictionary

        @param client: salt.client.ssh.SSH object
        @returns - Dictionary representing response

        """
        ret = {}
        for minion_ret in client.handle_ssh():
            ret.update(minion_ret)
        return ret

    def run(self, arg_str, func="cmd.run_all", target='*'):
        """
        Joins func and arg_str. Creates the options, client, and executes
        the client's request before returning the clients resp

        @TODO - Stop hijacking stderr. Only hijacking for the moment to hide
            a warning from salt-ssh abount an address already in use.  Should
            fix this then stop hijacking stderr.

        """
        old_stderr = sys.stderr
        try:
            arg_str = ' '.join([func, arg_str])
            options = self._options(arg_str, target=target)
            sys.stderr = open(os.devnull, 'w')
            client = self._client(options)
            resp = self._execute(client)
        finally:
            sys.stderr = old_stderr
        return resp

    def get_minions(self):
        """
        Attempts to target every salt-ssh minion. Instructs every ssh minion
        to run a test.ping. Returns a dictionary of every minion that returned
        true.

        @return - Dictionary

        """
        print "Getting minions..."
        minions = {}
        resp = self.run("", func="test.ping")
        for resp_id, resp_value in resp.iteritems():
            if resp_value is True:
                minions[resp_id] = {'ssh_id': resp_id}
        return minions

    def get_hostnames(self):
        """
        Executes the cmd 'hostname' on all ssh minions. The hostname will be
        used as the minion id on normal salt.

        @return - Dictionary

        """
        print "Updating minions with hostnames..."
        resp = self.run('hostname', func='cmd.run_all')
        for resp_id, hostname in resp.iteritems():
            if hostname and (resp_id in self.minions):
                self.minions[resp_id].update(hostname=hostname)

    def validate_bootstrapped(self, text):
        """
        Validates that the stdout of running the bootstrap script indicates
        that salt-minion was successfully installed.

        @param text - String of stdout sent back by salt-ssh
        @return boolean - True for success, False otherwise
        """
        return 'Salt installed!' in text

    def bootstrap_minions(self):
        """
        Runs the minion bootstrap script on all ssh minions

        """
        print "Bootstrapping minions..."
        shell_cmd = 'curl -L http://bootstrap.saltstack.org | sudo sh -s -- -X'
        resp = self.run(shell_cmd, 'cmd.run_all')
        for resp_id, resp_value in resp.iteritems():
            if resp_id in self.minions:
                bootstrapped = self.validate_bootstrapped(resp_value)
                self.minions[resp_id]['bootstrapped'] = bootstrapped
                if not bootstrapped:
                    print "Was unable to bootstrap salt on %s:" % resp_id
                    print resp_value

    def validate_set_master(self, text):
        """
        Checks stdout of the commmand to appending the master setting to the
        salt-minion config of a minion.

        @param text - String of stdout from command to set the master

        """
        return 'Wrote 1 lines to' in text

    def set_master(self):
        """
        Sets the master in the salt minion config on the ssh minion.
        @TODO - Change location of minion config to be configurable.

        """
        print "Setting master on minions..."
        minion_config_path = "/etc/salt/minion"
        arg_str = "%s \"master: %s\"" % (minion_config_path, self.master_ip)
        resp = self.run(arg_str, func="file.append")
        for resp_id, resp_value in resp.iteritems():
            if resp_id in self.minions:
                set_master = self.validate_set_master(resp_value)
                self.minions[resp_id]['set_master'] = set_master
                if not set_master:
                    print "Unable to set master for %s" % resp_id

    def remove_file(self, dst, target='*'):
        """
        Removes the file dst(destination) from the minion

        @param dst - String destination file name
        @param minion - Minion dictionary containing the minion's ssh-id

        """
        print "Removing %s on %s..." % (dst, target)
        arg_str = "file.absent name=\"%s\"" % dst
        resp = self.run(arg_str, func="state.single", target=target)
        for resp_id, resp_value in resp.iteritems():
            if resp_id in self.minions:
                if not resp_value.values()[0]['result']:
                    print "Unable to remove %s on %s" % (dst, target)

    def touch_file(self, dst, target='*'):
        """
        Touches the file dst on the specified target

        @param dst - String destination file on minion
        @param target - String target

        """
        print "Touching %s on %s..." % (dst, target)
        arg_str = "name=\"%s\"" % dst
        resp = self.run(arg_str, func='file.touch', target=target)
        for resp_id, resp_value in resp.iteritems():
            if resp_id in self.minions:
                if resp_value is not True:
                    print "Unable to touch %s on %s" % (dst, target)

    def send_file(self, src, dst, target='*'):
        """
        Sends a local file at src to dst on target. Currently removes the
        existing file at location dst, touches that location, then appends
        the contents of src to dst. cp.file_get and file.managed do not seem
        to be able to resolve the salt:// uri's yet through salt-ssh.

        @param src - String source file location
        @param dst - String destination file locatrion
        @param target - String target

        """
        # Get the file contents
        try:
            f = open(src)
            contents = f.readlines()
            f.close()
        except Exception:
            print (
                "Could not open file %s to send to %s on %s"
                % (src, dst, minion['ssh_id'])
            )
            return

        # Convert for consumption
        contents = ['"%s"' % line.rstrip() for line in contents]
        contents = "[" + ",".join(contents) + "]"

        # Remove the destination file if it exists
        self.remove_file(dst, target)

        # Touch the file to create an empty file
        self.touch_file(dst, target)

        print "Writing  %s on %s..." % (dst, target)
        # Append the contents of source file to destination
        arg_str = "file.append \"%s\" text='%s'" % (dst, contents)
        resp = self.run(arg_str, func='state.single', target=target)
        for resp_id, resp_value in resp.iteritems():
            if resp_id in self.minions:
                if not resp_value.values()[0]['result']:
                    print (
                        "Unable to send file %s to %s on %s"
                        % (src, dst, minion['ssh_id'])
                    )

    def send_file_sftp(self, src, dst, minion):

        print "Sending file via sftp %s to %s on %s" % (src, dst, minion['ssh_id'])

        host = self.roster.get(minion['ssh_id'])
        if host is None:
            print "Did not find minion %s in the roster." % minion['ssh_id']

        host = self.roster[minion['ssh_id']]
        port = 22
        transport = paramiko.Transport((host['host'], port))
        transport.connect(username=host['user'], password=host['passwd'])
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(src, dst)
        sftp.close()
        transport.close()

    def move_file(self, src, dst, target='*'):
        
        print "Moving %s to %s on %s..." % (src, dst, target)
        arg_str = "mv %s %s" % (src, dst)
        resp = self.run(arg_str, func="cmd.run_all", target=target)
        for resp_id, resp_value in resp.iteritems():
            if resp_value:
                print "Unable to move %s to %s on %s:" % (src, dst, target)
                print resp_value

    def gen_keys(self):
        """
        Generates public, private key pairs for each minion.
        Both public and private keys are published to the minion.
        The public key is also pushed to the master pki dir under the minion's
        hostname.

        """
        # Keys temporarilty written to the cwd
        cwd = os.getcwd()

        # Location for public keys on master
        master_pki_dir = os.path.join(MASTER_OPTIONS.get('pki_dir'), 'minions')

        # Location for public and private key on minion
        minion_pki_dir = '/etc/salt/pki/minion/'

        keysize = MASTER_OPTIONS.get('keysize')

        for ssh_id, minion in self.minions.iteritems():

            # Generate keys using salt crypt
            # after, keys should be ./{ssh_id}.pub and ./{ssh_id}.pem
            salt.crypt.gen_keys(cwd, ssh_id, keysize)

            # copy public key to pki dir under minion hostname
            src = os.path.join(cwd, "%s.pub" % ssh_id)
            dst = os.path.join(master_pki_dir, minion['hostname'])
            try:
                shutil.copy(src, dst)
            except Exception:
                print (
                    "Unable to save the public key for %s with hostname %s"
                    % (ssh_id, minion['hostname'])
                )
                continue

            # Copy private key to minion
            # Send file via sftp
            src = os.path.join(cwd, "%s.pem" % minion['ssh_id'])
            dst = os.path.join('/tmp', 'minion.pem')
            self.send_file_sftp(src, dst, minion)
            
            # move file to location requiring sudo
            src = dst
            dst = os.path.join(minion_pki_dir, 'minion.pem')
            self.move_file(src, dst, minion['ssh_id'])
            #self.send_file(src, dst, minion['ssh_id'])

            # Copy public key to minion
            # Send file via sftp
            src = os.path.join(cwd, "%s.pub" % minion['ssh_id'])
            dst = os.path.join('/tmp', 'minion.pub')
            self.send_file_sftp(src, dst, minion)

            # Move file to secure location requiring sudo
            src = dst
            dst = os.path.join(minion_pki_dir, 'minion.pub')
            self.move_file(src, dst, minion['ssh_id'])
            #self.send_file(src, dst, minion['ssh_id'])

            # Delete the generated public key
            try:
                dst = os.path.join(cwd, '%s.pub' % ssh_id)
                os.remove(dst)
            except Exception:
                print "Warning: %s.pub may not have been deleted." % ssh_id

            # Delete generated private key
            try:
                dst = os.path.join(cwd, '%s.pem' % ssh_id)
                os.remove(dst)
            except Exception:
                print "Warning: %s.pem may not have been removed." % ssh_id

    def restart_minion_service(self):
        """
        Restarts the salt-minion service on all minions.

        """
        arg_str = 'salt-minion'
        resp = self.run(arg_str, func="service.restart")
        for resp_id, resp_value in resp.iteritems():
            if resp_id in self.minions:
                print "Restarted salt-minion on %s" % resp_id

if __name__ == "__main__":
    # Create an arg parser
    parser = argparse.ArgumentParser(
        description="Install salt-minion on minions via salt-ssh",
        prog="python minion_installer.py"
    )

    # Add option argument for the master interface
    parser.add_argument(
        '--master-interface',
        default='eth0',
        type=str,
        help="Set the master interface(Default eth0)"
    )

    # Add flag to indicate test mode only
    parser.add_argument(
        '-test',
        action="store_true",
        default=False,
        help="Test connectivty to minions in roster"
    )

    # Parse args
    args = parser.parse_args()
    installer = Installer(master_interface=args.master_interface)

    # Check for test mode
    if (args.test):
        print (
            "Testing connectivity of minions defined in roster."
            "Showing minions I can talk to:"
        )
        minions = installer.get_minions()
        for minion_id in minions:
            print "%s" % minion_id
        exit()

    # Install on minions
    installer.install()
