import contextlib
import psycopg2
import transaction
import unittest
import uuid

class Psycopg2TransactionTests(unittest.TestCase):

    def setUp(self):
        self.__tname = 't' + uuid.uuid1().hex
        conn, cursor = self.__connect()
        cursor.execute("create table %s (v int)" % self.__tname); conn.commit()
        cursor.close(); conn.close()

    def tearDown(self):
        conn, cursor = self.__connect()
        cursor.execute("drop table "  + self.__tname); conn.commit()
        cursor.close(); conn.close()

    def __connect(self):
        conn = psycopg2.connect('')
        return conn, conn.cursor()

    def test_normal(self):
        import psycopg2transaction

        conn, cursor = self.__connect()
        psycopg2transaction.join(conn)
        cursor.execute("insert into %s values (1)" % self.__tname)
        transaction.commit()
        cursor.close(); conn.close()

        conn, cursor = self.__connect()
        cursor.execute("select * from " + self.__tname)
        self.assertEqual([(1,)], list(cursor))
        cursor.close(); conn.close()

    def test_non_threaded_tm(self):
        import psycopg2transaction

        tm = transaction.TransactionManager()
        conn, cursor = self.__connect()
        psycopg2transaction.join(conn, tm.get())
        cursor.execute("insert into %s values (1)" % self.__tname)
        tm.commit()
        cursor.close(); conn.close()

        conn, cursor = self.__connect()
        cursor.execute("select * from " + self.__tname)
        self.assertEqual([(1,)], list(cursor))
        cursor.close(); conn.close()

    def test_abort_before_prepare(self):
        import psycopg2transaction

        conn, cursor = self.__connect()
        psycopg2transaction.join(conn)
        cursor.execute("insert into %s values (1)" % self.__tname)
        transaction.abort()
        cursor.execute("select * from " + self.__tname)
        self.assertEqual([], list(cursor))
        cursor.close(); conn.close()

    def test_abort_after_prepare(self):
        import psycopg2transaction

        conn, cursor = self.__connect()
        psycopg2transaction.join(conn)
        cursor.execute("insert into %s values (1)" % self.__tname)

        transaction.get().join(BadDM())
        with self.assertRaises(ValueError):
            transaction.commit()
        transaction.abort()
        cursor.execute("select * from " + self.__tname)
        self.assertEqual([], list(cursor))
        cursor.close(); conn.close()

    def test_abort_before_begin(self):
        import psycopg2transaction

        conn, cursor = self.__connect()
        psycopg2transaction.join(conn)
        cursor.execute("insert into %s values (1)" % self.__tname)

        transaction.get().join(BadDM(True))
        with self.assertRaises(ValueError):
            transaction.commit()
        transaction.abort()
        cursor.execute("select * from " + self.__tname)
        self.assertEqual([], list(cursor))
        cursor.close(); conn.close()

    def test_connection_management(self):
        import psycopg2transaction
        conn = psycopg2transaction.join('')
        with contextlib.closing(conn.cursor()) as cursor:
            cursor.execute("insert into %s values (1)" % self.__tname)
        self.assertTrue(psycopg2transaction.join('') is conn)
        transaction.commit()
        self.assertTrue(conn.closed)

        conn = psycopg2transaction.join('')
        transaction.abort()
        self.assertTrue(conn.closed)

    def test_connection_notify(self):
        import psycopg2transaction

        lconn, lcursor = self.__connect()
        lconn.autocommit = True
        lcursor.execute("LISTEN " + self.__tname)

        conn = psycopg2transaction.join('', notify=self.__tname)
        with contextlib.closing(conn.cursor()) as cursor:
            cursor.execute("insert into %s values (1)" % self.__tname)
        self.assertTrue(psycopg2transaction.join('') is conn)
        transaction.commit()
        self.assertTrue(conn.closed)

        lconn.poll()
        self.assertEqual(1, len(lconn.notifies))
        lcursor.close()
        lconn.close()

class BadDM:

    def __init__(self, bad_early=False):
        self.bad_early = bad_early

    def tpc_begin(self, trans):
        if self.bad_early:
            self.bad_early = False
            raise ValueError('heck no')

    commit = abort = tpc_abort = tpc_begin

    def tpc_vote(self, trans):
        raise ValueError('heck no')

    def sortKey(self):
        return 'bad'
