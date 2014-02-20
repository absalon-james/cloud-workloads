import threading


class NoAvailableMinionException(Exception):
    """Exception for when no minions are available."""

    def __init__(self, role=None):
        """
        Minions can be reserved or not.  Message changes slightly.
        @param role: String reserved role

        """
        if role is not None:
            msg = "No available minion for role %s." % role
        else:
            msg = "No available minion."

        super(NoAvailableMinionException, self).__init__(msg)


class LockedPoolException(Exception):
    """
    Exception is thrown when a non blocking request is made and
    a lock is unable to be obtained on the pool.

    """
    def __init__(self):
        msg = "Minion pool is locked."
        super(LockedPoolException, self).__init__(msg)


class MinionPool(object):
    """
    Class that maintains a list of minions, reserved or otherwise and
    provides synchronized access to the list.

    """

    def __init__(self, minions, reservations=None):
        """
        Initializes the minion pool.

        @param minions: List of available minions to use
        @param reservations: Dictionary of roles to a list of minion ids

        """
        self._lock = threading.Lock()
        self.reservations = reservations or {}

        self._regular = []
        self._reserved = []
        for minion in minions:
            self.put_minion(minion)

    def put_minion(self, minion, blocking=True):
        """
        Puts the minion into the pool.

        @param minion: Minion to place back into the pool
        @param blocking: Boolean indicating whether or not to wait on a lock.
        @raises LockedPoolException

        """
        locked = self._lock.acquire(blocking)
        if not locked:
            raise LockedPoolException()
        try:
            for reservation, ids in self.reservations.iteritems():
                if minion.id_ in ids:
                    addto = self._reserved
                    break
            else:
                addto = self._regular
            addto.append(minion)
        finally:
            self._lock.release()

    def _get_regular(self):
        """
        Returns a regular minion if available

        @raises NoAvailableMinionException
        @return: Minion

        """
        if len(self._regular) > 0:
            return self._regular.pop(0)
        raise NoAvailableMinionException()

    def _get_reserved(self, role):
        """
        Returns a reserved minion if availble.

        @param role: String role
        @raises NoAvailableMinionException
        @return: Minion

        """
        ids = self.reservations.get(role, None)
        if ids is None:
            raise Exception("The role %s is not a reserved role." % role)

        for i, minion in enumerate(self._reserved):
            if minion.id_ in ids:
                return self._reserved.pop(i)
        raise NoAvailableMinionException(role=role)

    def get_minion(self, role=None, blocking=True):
        """
        Gets a minion from the pool.

        @param role: Role indicating a reserved minion
        @param blocking: Boolean indicating whether or not to wait on a lock.
        @raises LockedPoolException

        """

        locked = self._lock.acquire(blocking)
        if not locked:
            raise LockedPoolException()
        try:
            if role is None:
                minion = self._get_regular()
            else:
                minion = self._get_reserved(role)
        finally:
            self._lock.release()
        return minion

    def get_info(self):
        """
        Returns a dictionary containing pool stats

        @return: dictionary

        """

        available_minions = ', '.join([m.id_ for m in self._regular])
        reserved = ', '.join([m.id_ for m in self._reserved])

        return {
            'regular_available': len(self._regular),
            'regular_minions': available_minions,
            'reserved': len(self._reserved),
            'reserved_minions': reserved,
            'reservations': self.reservations
        }
