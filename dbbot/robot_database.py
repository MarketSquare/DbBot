import sqlite3

from .logger import Logger


class RobotDatabase(object):

    def __init__(self, db_file_path, verbose):
        self._verbose = Logger('Database', verbose)
        self._connection = self._connect(db_file_path)
        self._configure()

    def _connect(self, db_file_path):
        self._verbose('- Establishing database connection')
        return sqlite3.connect(db_file_path)

    def _configure(self):
        self._set_pragma('page_size', 4096)
        self._set_pragma('cache_size', 10000)
        self._set_pragma('synchronous', 'NORMAL')
        self._set_pragma('journal_mode', 'WAL')

    def _set_pragma(self, name, value):
        sql_statement = 'PRAGMA %s=%s' % (name, value)
        self._connection.execute(sql_statement)

    def close(self):
        self._verbose('- Closing database connection')
        self._connection.close()
