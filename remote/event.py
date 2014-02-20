import os
from multiprocessing import Process, Manager
from salt.config import master_config
from salt.client.api import APIClient

MASTER_CONFIG_PATH = os.environ.get('SALT_MASTER_CONFIG', '/etc/salt/master')
MASTER_OPTIONS = master_config(MASTER_CONFIG_PATH)
POLLER_MANAGER = Manager()


class EventStore(object):
    """
    Helps to provide synchronized access to Manager.dict() object
    which stores event information.

    The event store keys event information by job id(jid). The event store
    maintains a list of event returns at each jid location. New events
    are added to the end of the list. Event returns are retrieved one at
    a time by popping off the front of the list.

    """
    def __init__(self):
        """
        Object constructor

        """
        self._store = POLLER_MANAGER.dict()
        self._lock = POLLER_MANAGER.Lock()

    def store_event(self, key, event):
        """
        Adds an event return to the end of the list stored at location
        key. Locks the event store while storing.

        @param key - Key to store information at
        @param event - Dictionary of information.

        """
        try:
            self._lock.acquire()
            events = self._store.get(key, [])
            events.append(event)
            self._store[key] = events
        finally:
            self._lock.release()

    def get_event(self, key):
        """
        Returns the oldest event return stored at location key. The event
        return is popped off the beginning of the list.

        @return key - String key
        @return - Dictionary of event information or None

        """
        event = None
        try:
            self._lock.acquire()
            events = self._store.get(key, [])
            if len(events):
                event = events.pop(0)
            self._store[key] = events
        finally:
            self._lock.release()
        return event


class JobPoller(Process):
    """
    Subclass of process that has one purpose and that is to constantly poll
    the salt master event queue for job updates

    """
    # Set this key int he controls dict to signal the process to stop
    STOP_KEY = '_END_POLLER_'

    def __init__(self, event_store, event_wait=1):
        """
        Constructor for the job poller

        @param event_store - EventStore object to save job updates
        @param event_wait - Time to wait on the event queue in seconds for
            each polling.

        """
        super(JobPoller, self).__init__()
        self.event_wait = event_wait
        self.event_store = event_store
        self.controls = POLLER_MANAGER.dict()

    def signal_stop(self):
        """
        Signals the process to stop. The main loop of the process
        will check for this once every iteration

        """
        self.controls[self.STOP_KEY] = True

    def should_stop(self):
        """
        Checks to see if this process should stop.

        @return Boolean true for yes, Boolean false otherwise
        """
        return self.controls.get(self.STOP_KEY, False)

    def run(self):
        """
        The run portion of the process. Runs until signalled to stop

        """
        client = APIClient(opts=MASTER_OPTIONS)
        while True:
            event = client.get_event(tag='', wait=self.event_wait)

            # Continue if no event was found
            if event is None:
                continue

            jid = event.get('jid')
            ret = event.get('return')
            if jid is not None and ret is not None:
                self.event_store.store_event(jid, event)

            # Break if signalled to stop
            if self.should_stop():
                break
