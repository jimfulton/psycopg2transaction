=====================================
psycopg2 integration with transaction
=====================================

This package provides two-phase commit integration between psycopg2
and the transaction package.

Sample usage::

  >>> import psycopg2, psycopg2transaction, transaction

  >>> conn = psycopg2.connect(mydsn)
  >>> trans = transaction.get()
  >>> psycopg2transaction.join(conn, trans)

  >>> ... do things with the psycopg2 connection

  >>> transaction.commit()

This is just an example. The connection might come from a pool or
otherwise already exist, as long as it is in a `suitable state to start
a distributed transaction
<http://initd.org/psycopg/docs/connection.html#connection.tpc_begin>`_.

Similarly, the transaction may come from the thread-local transaction
manager, as shown above, or from an application-managed transaction
manager.

The critical line in the example above is::

  >>> psycopg2transaction.join(conn, trans)

The work done in the connection is committed by calling the
transaction's commit method, typically by calling ``commit`` on the
transaction's manager, as shown above.

If you use a thread-local transaction manager (as in the example
above), you can omit the transaction argumet to ``join``::

  >>> psycopg2transaction.join(conn)

Connection management
=====================

Limited connection management is provided::

  >>> dsn = 'dbname=test'
  >>> conn = psycopg2transaction.join(dsn)
  ...
  >>> conn = psycopg2transaction.join(dsn)
  ...
  >>> transaction.commit()

If you pass a connection string rather than a connection to ``join``, a
connection will be opened for you and closed when the transaction is
committed.  If ``join`` is called multiple times with the same connection
string, then the same connection is used and returned.

Using Postgres notify
=====================

You can't use two-phase commit in postgres transactions in which
you've used NOTIFY (or LISTEN or UNLISTEN).  You can cause NOTIFY to
be used after a transaction has committed, but before a managed
connection has been closed by passing a ``notify`` argument to join
with a name of a notification or a sequence of string notification
named.  The strings may be simple names, or names followed by a comma
and string data, as would follow NOTIFY in a notify expression::

  >>> conn = psycopg2transaction.join(dsn, notify='myjobs')
