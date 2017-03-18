import contextlib
import psycopg2
import transaction
import uuid

class DataManager:

    on_complete = ()
    notifies = None

    def __init__(self, conn, trans=None, on_complete=None):
        self.xid = uuid.uuid1().hex
        conn.tpc_begin(self.xid)
        self.conn = conn
        trans.join(self)
        if on_complete is not None:
            self.on_complete = (on_complete,)

    def tpc_begin(self, trans):
        pass

    commit = tpc_begin

    def tpc_vote(self, trans):
        self.conn.tpc_prepare()

    def tpc_finish(self, trans):
        self.conn.tpc_commit()
        self.xid = None
        if self.notifies:
            with contextlib.closing(self.conn.cursor()) as cursor:
                cursor.execute(';\n'.join('NOTIFY ' + s for s in self.notifies))
            self.conn.commit()

        for f in self.on_complete:
            f()

    def tpc_abort(self, trans):
        if self.xid:
            self.conn.tpc_rollback()
            self.xid = None
            for f in self.on_complete:
                f()

    abort = tpc_abort

    def sortKey(self):
        return self.conn.dsn

def join(conn, trans=None, notify=None):
    if trans is None:
        trans = transaction.get()

    if isinstance(conn, str):
        dsn = conn
        try:
            dms = trans.data(DataManager)
        except KeyError:
            dms = {}
            trans.set_data(DataManager, dms)

        if dsn in dms:
            dm = dms[dsn]
        else:
            conn = psycopg2.connect(dsn)
            dm = DataManager(conn, trans, on_complete=conn.close)
            dms[dsn] = dm

        if notify:
            notifies = dm.notifies
            if not notifies:
                notifies = dm.notifies = set()

            if isinstance(notify, str):
                notifies.add(notify)
            else:
                notifies.update(set(notify))

        return dm.conn
    else:
        DataManager(conn, trans)
