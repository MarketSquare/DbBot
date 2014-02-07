#  Copyright 2013-2014 Nokia Solutions and Networks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import sqlite3

from .logger import Logger


class RobotDatabase(object):

    def __init__(self, db_file_path, verbose_stream):
        self._verbose = Logger('Database', verbose_stream)
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
