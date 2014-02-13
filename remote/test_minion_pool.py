import unittest
import uuid

from pool import MinionPool, NoAvailableMinionException, LockedPoolException
from minion import Minion

class FakeMinion(object):
    def __init__(self):
        self.id_ = str(uuid.uuid4())

class TestMinionPool(unittest.TestCase):

    def spawn_minion(self):
        return FakeMinion()

    def test_empty_no_reservations(self):
        pool = MinionPool([])
        self.assertEquals(len(pool._regular), 0)
        self.assertEquals(len(pool._reserved), 0)
        self.assertEquals(len(pool.reservations), 0)

    def test_empty_get(self):
        pool = MinionPool([])
        
        with self.assertRaises(NoAvailableMinionException):
            minion1 = pool.get_minion()

    def test_get_no_wait(self):
        
        pool = MinionPool([])
        pool._lock.acquire()
        try:
            with self.assertRaises(LockedPoolException):
                minion = pool.get_minion(blocking=False)
        finally:
            pool._lock.release()

    def test_get_regular_order(self):

        minion1 = self.spawn_minion()
        minion2 = self.spawn_minion()
        minion3 = self.spawn_minion()
        minions = [minion1, minion2, minion3]

        pool = MinionPool(minions)
        m1 = pool.get_minion()
        m2 = pool.get_minion()
        m3 = pool.get_minion()

        self.assertEquals(minion1.id_, m1.id_)
        self.assertEquals(minion2.id_, m2.id_)
        self.assertEquals(minion3.id_, m3.id_)

    def test_get_reserved(self):

        minion1 = FakeMinion()
        minion2 = FakeMinion()
        minion3 = FakeMinion()
        role1 = str(uuid.uuid4())
        reservations = {
            role1: [minion2.id_]
        }
        pool = MinionPool([minion1, minion2, minion3], reservations=reservations)
        m1 = pool.get_minion(role=role1)
        self.assertEquals(minion2.id_, m1.id_)
        with self.assertRaises(NoAvailableMinionException):
            m2 = pool.get_minion(role=role1)

    def test_put_no_wait(self):
        minion1 = FakeMinion()
        pool = MinionPool([])
        pool._lock.acquire()
        with self.assertRaises(LockedPoolException):
            pool.put_minion(minion1, blocking=False)
