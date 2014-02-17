import os
import salt
import time
from multiprocessing import Process, Manager
from salt.config import master_config
from salt.client.api import APIClient


MASTER_CONFIG_PATH = os.environ.get('SALT_MASTER_CONFIG', '/etc/salt/master')
MASTER_OPTIONS = master_config(MASTER_CONFIG_PATH)
POLLER_MANAGER = Manager()

class EventStore(object):

    def __init__(self):
        self._store = POLLER_MANAGER.dict()
        self._lock = POLLER_MANAGER.Lock()

    def store_event(self, key, event):
        try:
            self._lock.acquire()
            events = self._store.get(key, [])
            events.append(event)
            self._store[key] = events
        finally:
            self._lock.release()

    def get_event(self, key):
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

    STOP_KEY = '_END_POLLER_'

    def __init__(self, event_store, event_wait=1):
        super(JobPoller, self).__init__()
        self.event_wait = event_wait
        self.event_store = event_store
        self.controls = POLLER_MANAGER.dict()

    def signal_stop(self):
        self.controls[self.STOP_KEY] = True

    def should_stop(self):
        return self.controls.get(self.STOP_KEY, False)

    def run(self):
        client = salt.client.api.APIClient(opts=MASTER_OPTIONS)
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
