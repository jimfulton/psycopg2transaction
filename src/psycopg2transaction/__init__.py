import psycopg2
import transaction
import uuid

class DataManager:

    def __init__(self, conn, trans=None, on_complete=lambda: None):
        self.xid = uuid.uuid1().hex
        conn.tpc_begin(self.xid)
        self.conn = conn
        trans.join(self)
        self.on_complete = on_complete

    def tpc_begin(self, trans):
        pass

    commit = tpc_begin

    def tpc_vote(self, trans):
        self.conn.tpc_prepare()

    def tpc_finish(self, trans):
        self.conn.tpc_commit()
        self.xid = None
        self.on_complete()

    def tpc_abort(self, trans):
        if self.xid:
            self.conn.tpc_rollback()
            self.xid = None
            self.on_complete()

    abort = tpc_abort

    def sortKey(self):
        return self.conn.dsn

def join(conn, trans=None):
    if trans is None:
        trans = transaction.get()

    if isinstance(conn, str):
        dsn = conn
        try:
            conns = trans.data(DataManager)
        except KeyError:
            conns = {}
            trans.set_data(DataManager, conns)

        if dsn in conns:
            conn = conns[dsn]
        else:
            conn = psycopg2.connect(dsn)
            DataManager(conn, trans, on_complete=conn.close)
            conns[dsn] = conn

        return conn
    else:
        DataManager(conn, trans)
