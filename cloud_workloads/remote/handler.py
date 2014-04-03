class BaseJobException(Exception):
    """
    All exceptions raised by the below handler should subclass this class.
    This class provides a convenient way of unrolling other salt jobs that
    may be affected by the current salt job.

    """
    def __init__(self, job):
        """
        Constructor.  Calls make_msg and appends affect job output to the end.

        @param job - SaltJob

        """
        msg = self.make_msg(job)
        affected_msg = self.get_affected_msg(job)
        if affected_msg:
            msg += "\n" + affected_msg
        super(Exception, self).__init__(msg)

    def get_affected_msg(self, job):
        """
        Creates a newline/tab delimited list of affected SaltJob's

        @param job - SaltJob
        @return - String

        """
        msgs = []
        current = job.chain
        while current:
            msgs.append(self.get_affected_job_msg(current))
            current = current.chain
        if len(msgs) > 0:
            return ("This failure may have caused problems in a sequence."
                    "\n\t%s") % "\n\t".join(msgs)
        return ""

    def get_affected_job_msg(self, job):
        """
        Creates a message for a single salt job that may have been affected.

        @param job - Possible affected SaltJob
        @return - String

        """
        msg_tuple = (job.kwargs['fun'],
                     job.kwargs['arg'],
                     job.kwargs['tgt'])

        # The job may have started/finished but results may be off
        if job.jid:
            msg = ("Job %s with args %s to minions %s may have been"
                   " affected.") % msg_tuple
        # The job wasn't even published.
        else:
            msg = ("Job %s with args %s to minions %s may not have"
                   " started") % msg_tuple
        return msg


class PublishException(BaseJobException):
    """
    Exception for when a publish to salt returns an empty dictionary.

    """
    def make_msg(self, job):
        """
        Creates a newline delimited list of key, value pairs for the kmwargs
        sent to salt in an attempt to publish.

        @param job - SaltJob that failed to publish
        @return - String

        """
        kwargs = job.kwargs
        lines = ["%s: %s" % (key, value) for key, value in kwargs.iteritems()]
        lines.sort()
        lines = "\n".join(lines)
        msg = "Unable to publish job to salt:\n%s" % lines
        return msg


class UnfinishedException(BaseJobException):
    """
    Exception for when a timeout has been reached and a published job has
    not completed in time.

    """
    def make_msg(self, job):
        """
        Creates a string identifying the job id, the arguments,
        the salt function, and the unfinished minions.

        @param job - Unfinished SaltJob
        @return - String

        """
        unfinished = job.minions.difference(job.finished_minions)
        msg_tuple = (job.jid,
                     job.kwargs['arg'],
                     job.kwargs['fun'],
                     list(unfinished))
        return ("Job %s did not finish. Sent args %s to function %s on"
                " minions %s") % msg_tuple


class UnsuccessfulException(BaseJobException):
    """
    Exception for when the field 'success' is False for any minion in
    the returns for a salt job.

    """
    def make_msg(self, job):
        """
        Creates a newline/tab delimited list of messages that identify the
        affected minion and possible cause for the False success field.

        @param job - SaltJob
        @return - String

        """
        events = [e for e in job.events.itervalues() if not e['success']]
        msgs = []
        for e in events:
            msgs.append("%s - %s" % (e['id'], e['return']))
        msgs = "\n\t".join(msgs)
        msg_tuple = (job.jid, job.kwargs['arg'], job.kwargs['fun'], msgs)
        return ("Job %s was unsuccessful. Sent args %s to"
                " function %s:\n%s") % msg_tuple


class RetcodeException(BaseJobException):
    """
    Exception for when returned retcodes are not a subset of the acceptable
    retcodes

    """
    def make_msg(self, job):
        """
        Creates a newline/tab delimited list of messages identifying
        minions with possible causes of bad retcodes.

        @param job - SaltJob
        @return - String

        """
        events = [e for e in job.events.itervalues() if e.get('retcode', 1)]
        msgs = "\n\t".join([self.event_msg(e) for e in events])
        msg_tuple = (job.jid,
                     job.kwargs['arg'],
                     job.kwargs['fun'],
                     msgs)
        return ("Job %s had unacceptable retcodes. Sent args %s to"
                " function %s:\n%s") % msg_tuple

    def event_msg(self, event):
        """
        Creates a string identifying the minion, offending retcode, and
        possible cause.

        @param event - Event dictionary with keys for id, retcode, and return
        @return String

        """
        # Return default msg
        return "%s had retcode %s: %s" % (event['id'],
                                          event['retcode'],
                                          event['return'])


class FailedStateSlsException(BaseJobException):
    """
    Special exception for when not everything in a return to the salt function
    state.sls is not a success.

    """
    def make_msg(self, job):
        """
        Creates a newline/tab delimited list of items that have failed in the
        call to state.sls

        @param job - SaltJob
        @return - String

        """
        msgs = self.event_msgs(job)
        msgs = "\n\t".join(msgs)
        msgs = "\n\t" + msgs
        msg_tuple = (job.jid, job.kwargs['arg'], job.kwargs['fun'], msgs)
        return "Job %s failed. Sent args %s to function %s:%s" % msg_tuple

    def event_msgs(self, job):
        """
        Creates a list of strings that identify failures within a call to
        state.sls

        @param job - SaltJob
        @return - List of strings

        """
        msgs = []
        for minion_id, event in job.events.iteritems():
            for key, event_ret in event['return'].iteritems():
                if not event_ret['result']:
                    (module_id, state_id, name, method) = key.split("_|-")
                    msg_tuple = (minion_id,
                                 module_id,
                                 method,
                                 name,
                                 event_ret['comment'])
                    msgs.append("%s: %s.%s - %s - %s" % msg_tuple)
        return msgs


class Handler(object):
    """
    Helps handle reporting and validation with various aspects of interacting
    with salt.

    Handles publishing, job returns, and certain exceptions
    """
    # Maps salt functions to handler method suffixes
    handle_map = {
        'state.sls': 'state',
        'saltutil.sync_states': 'sync_state',
        'cmd.run_all': 'cmd_run',
        'grains.setval': 'grains_setval'
    }

    def get_func(self, prefix, salt_func):
        """
        Maps a salt function and a handler function prefix to a member function
        of the handler.

        @param prefix - String prefix examples: 'report_publish',
            'report_finish', etc.
        @param salt_func - String salt function name.  example: 'state.sls',
            'cmd.run_all', etc.
        @return - Matched functions or None

        """
        suffix = self.handle_map.get(salt_func, 'default')
        handler_func_name = '_'.join([prefix, suffix])
        func = getattr(self, handler_func_name)
        return func

    ##########################################################
    #### Publishes ###########################################
    ##########################################################

    def report_publish_default(self, job, pub_data):
        """
        Default report publisher

        @param job - SaltJob
        @param pub_data - Dictionary containing job id and minions

        """
        # Nothing for now
        pass

    def report_publish_grains_setval(self, job, pub_data):
        """
        Report publisher for grains.setval

        @param job - SaltJob
        @param pub_data - Dictionary containing jid and minions

        """
        msg_tuple = (
            pub_data['jid'],
            pub_data['minions'],
            job.kwargs['arg'][0],
            job.kwargs['arg'][1]
        )
        print "Job %s: %s - Setting grain %s to %s" % msg_tuple

    def report_publish_state(self, job, pub_data):
        """
        Report publisher for state.sls

        @param job - SaltJob
        @param pub_data - Dictionary containing job id and minions

        """
        kwargs = job.kwargs
        msg_tuple = (pub_data['jid'], pub_data['minions'], kwargs['arg'][0])
        print "Job %s: %s - Applying %s " % msg_tuple

    def report_publish_sync_state(self, job, pub_data):
        """
        Report publisher for saltutil.sync_states

        @param job - SaltJob
        @param pub_data - Dictionary containing job id and minions

        """
        msg_tuple = (pub_data['jid'], pub_data['minions'])
        print "Job %s: %s - Syncing states" % msg_tuple

    def report_publish_cmd_run(self, job, pub_data):
        """
        Report publisher for cmd.run, cmd.run_all

        @param job - SaltJob
        @param pub_data - Dictionary containing job id and minions

        """
        msg_tuple = (
            pub_data['jid'],
            pub_data['minions'],
            job.kwargs['arg'][0]
        )
        print "Job %s: %s - Running: %s" % msg_tuple

    ##########################################################
    #### Finishers ###########################################
    ##########################################################

    def report_finish_default(self, job):
        """
        Default report finisher

        @param job - SaltJob

        """
        pass

    def report_finish_grains_setval(self, job):
        """
        Report finisher for grains.setval

        @param job - SaltJob

        """
        msg_tuple = (
            job.jid,
            list(job.minions),
            job.kwargs['arg'][0],
            job.kwargs['arg'][1]
        )
        print "Job %s: %s - Set grain %s to %s" % msg_tuple

    def report_finish_state(self, job):
        """
        Report finisher for state.sls

        @param job - SaltJob

        """
        msg_tuple = (job.jid, list(job.minions), job.kwargs['arg'][0])
        print "Job %s: %s - Applied state %s" % (msg_tuple)

    def report_finish_sync_state(self, job):
        """
        Report finisher for saltutil.sync_states

        @param job - SaltJob

        """
        print "Job %s: %s - States synced" % (job.jid, list(job.minions))

    def report_finish_cmd_run(self, job):
        """
        Report finisher for cmd.run and cmd.run_all

        @param job - SaltJob
        """
        msg_tuple = (job.jid, list(job.minions), job.kwargs['arg'][0])
        print "Job %s: %s - Finished running: %s" % msg_tuple

    ##########################################################
    #### Handlers ############################################
    ##########################################################

    def handle_publish(self, job, pub_data):
        """
        Handles publishes.

        @param job - SaltJob
        @param pub_data - Dictionary containing job id and minions

        """
        kwargs = job.kwargs
        # validate the publish - Should be a non empty dict
        if not pub_data:
            raise PublishException(job)

        # Report the publish
        report_func = self.get_func('report_publish', kwargs['fun'])
        report_func(job, pub_data)

    def handle_finish(self, job):
        """
        Handles finishing jobs

        @param job - SaltJob

        """
        kwargs = job.kwargs
        report_func = self.get_func('report_finish', kwargs['fun'])
        report_func(job)

    def handle_unfinished(self, job):
        """
        Handles jobs that are unfinished

        @param job - SaltJob

        """
        raise UnfinishedException(job)

    def handle_unsuccessful(self, job):
        """
        Handles jobs that are unsuccessful

        @param job - SaltJob
        """
        raise UnsuccessfulException(job)

    def handle_retcodes(self, job):
        """
        Handles jobs that have returned with unacceptable retcodes.

        @param job - SaltJob

        """
        raise RetcodeException(job)

    def handle_failed_state_sls(self, job):
        """
        Handles jobs that failed state.sls.

        @param job
        """
        raise FailedStateSlsException(job)
