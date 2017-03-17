import transaction
import uuid

class DataManager:

    def __init__(self, conn, trans=None):
        if trans is None:
            trans = transaction.get()

        self.xid = uuid.uuid1().hex
        conn.tpc_begin(self.xid)
        self.conn = conn
        trans.join(self)

    def tpc_begin(self, trans):
        pass

    commit = tpc_begin

    def tpc_vote(self, trans):
        self.conn.tpc_prepare()

    def tpc_finish(self, trans):
        self.conn.tpc_commit()
        self.xid = None

    def tpc_abort(self, trans):
        if self.xid:
            self.conn.tpc_rollback()
            self.xid = None

    abort = tpc_abort

    def sortKey(self):
        return self.conn.dsn

join = DataManager
