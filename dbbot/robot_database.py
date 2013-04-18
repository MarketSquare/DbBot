import sqlite3

from .logger import Logger


class RobotDatabase(object):
    def __init__(self, db_file_path, be_verbose=False):
        self._logger = Logger('Database') if be_verbose else None
        self._connection = self._connect(db_file_path)
        self._connection.row_factory = sqlite3.Row
        self._configure()
        self._init_schema()

    def _verbose(self, message):
        if self._logger:
            self._logger(message)

    def close(self):
        self._verbose('- Closing database connection')
        self._connection.close()

    def commit(self):
        self._verbose('- Committing changes into database')
        self._connection.commit()

    def fetch_id(self, table_name, criteria):
        sql_statement = 'SELECT id FROM %s WHERE ' % table_name
        sql_statement += ' AND '.join('%s=?' % key for key in criteria.keys())
        return self._connection.execute(sql_statement, criteria.values()).fetchone()[0]

    def failed_suites(self):
        sql_statement = '''
            SELECT count() as count, suites.id, suites.name, suites.source
            FROM suites, suite_status
            WHERE suites.id == suite_status.suite_id AND
            suite_status.status == "FAIL"
            GROUP BY suites.source
        '''
        return self._connection.execute(sql_statement).fetchall()

    def failed_tests_for_suite(self, suite_id):
        sql_statement = '''
            SELECT count() as count, tests.id, tests.name, tests.suite_id
            FROM tests, test_status
            WHERE tests.id == test_status.test_id AND
            tests.suite_id == ? AND
            test_status.status == "FAIL"
            GROUP BY tests.name
        '''
        return self._connection.execute(sql_statement, [suite_id]).fetchall()

    def failed_keywords_for_test(self, test_id):
        sql_statement = '''
            SELECT count() as count, keywords.name, keywords.type
            FROM keywords, keyword_status
            WHERE keywords.id == keyword_status.keyword_id AND
            keywords.test_id == ? AND
            keyword_status.status == "FAIL"
            GROUP BY keywords.name, keywords.type
        '''
        return self._connection.execute(sql_statement, [test_id]).fetchall()

    def insert(self, table_name, criteria):
        sql_statement = self._format_insert_statement(table_name, criteria.keys())
        cursor = self._connection.execute(sql_statement, criteria.values())
        return cursor.lastrowid

    def insert_or_ignore(self, table_name, criteria):
        sql_statement = self._format_insert_statement(table_name, criteria.keys(), 'IGNORE')
        self._connection.execute(sql_statement, criteria.values())

    def insert_many_or_ignore(self, table_name, column_names, values):
        sql_statement = self._format_insert_statement(table_name, column_names, 'IGNORE')
        self._connection.executemany(sql_statement, values)

    def _format_insert_statement(self, table_name, column_names, on_conflict='ABORT'):
        return 'INSERT OR %s INTO %s (%s) VALUES (%s)' % (
            on_conflict,
            table_name,
            ','.join(column_names),
            ','.join('?' * len(column_names))
        )

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

    def _init_schema(self):
        self._verbose('- Initializing database schema')
        self._create_table('test_runs', {
            'source_file': 'TEXT NOT NULL',
            'generator': 'TEXT NOT NULL',
            'started_at': 'DATETIME NOT NULL',
            'finished_at': 'DATETIME NOT NULL',
            'imported_at': 'DATETIME NOT NULL',
        }, ('generator', 'source_file', 'started_at', 'finished_at'))
        self._create_table('test_run_status', {
            'test_run_id': 'INTEGER NOT NULL REFERENCES test_runs',
            'name': 'TEXT NOT NULL',
            'elapsed': 'INTEGER NOT NULL',
            'failed': 'INTEGER NOT NULL',
            'passed': 'INTEGER NOT NULL'
        }, ('test_run_id', 'name'))
        self._create_table('test_run_errors', {
            'test_run_id': 'INTEGER NOT NULL REFERENCES test_runs',
            'level': 'TEXT NOT NULL',
            'timestamp': 'DATETIME NOT NULL',
            'content': 'TEXT NOT NULL'
        }, ('test_run_id', 'level', 'content'))
        self._create_table('tag_status', {
            'test_run_id': 'INTEGER NOT NULL REFERENCES test_runs',
            'name': 'TEXT NOT NULL',
            'critical': 'INTEGER NOT NULL',
            'elapsed': 'INTEGER NOT NULL',
            'failed': 'INTEGER NOT NULL',
            'passed': 'INTEGER NOT NULL',
        }, ('test_run_id', 'name'))
        self._create_table('suites', {
            'suite_id': 'INTEGER REFERENCES suites',
            'xml_id': 'TEXT NOT NULL',
            'name': 'TEXT NOT NULL',
            'source': 'TEXT NOT NULL',
            'doc': 'TEXT NOT NULL'
        }, ('name', 'source'))
        self._create_table('suite_status', {
            'test_run_id': 'INTEGER REFERENCES test_runs',
            'suite_id': 'INTEGER REFERENCES suites',
            'elapsed': 'INTEGER NOT NULL',
            'failed': 'INTEGER NOT NULL',
            'passed': 'INTEGER NOT NULL',
            'status': 'TEXT NOT NULL'
        }, ('test_run_id', 'suite_id'))
        self._create_table('tests', {
            'suite_id': 'INTEGER NOT NULL REFERENCES suites',
            'xml_id': 'TEXT NOT NULL',
            'name': 'TEXT NOT NULL',
            'timeout': 'TEXT NOT NULL',
            'doc': 'TEXT NOT NULL'
        }, ('suite_id', 'name'))
        self._create_table('test_status', {
            'test_run_id': 'INTEGER REFERENCES test_runs',
            'test_id': 'INTEGER REFERENCES tests',
            'status': 'TEXT NOT NULL',
            'elapsed': 'INTEGER NOT NULL'
        }, ('test_run_id', 'test_id'))
        self._create_table('keywords', {
            'suite_id': 'INTEGER REFERENCES suites',
            'test_id': 'INTEGER REFERENCES tests',
            'keyword_id': 'INTEGER REFERENCES keywords',
            'name': 'TEXT NOT NULL',
            'type': 'TEXT NOT NULL',
            'timeout': 'TEXT NOT NULL',
            'doc': 'TEXT NOT NULL'
        }, ('name', 'type'))
        self._create_table('keyword_status', {
            'test_run_id': 'INTEGER REFERENCES test_runs',
            'keyword_id': 'INTEGER REFERENCES keyword',
            'status': 'TEXT NOT NULL',
            'elapsed': 'INTEGER NOT NULL'
        }, ('test_run_id', 'keyword_id'))
        self._create_table('messages', {
            'keyword_id': 'INTEGER NOT NULL REFERENCES keywords',
            'level': 'TEXT NOT NULL',
            'timestamp': 'DATETIME NOT NULL',
            'content': 'TEXT NOT NULL'
        }, ('keyword_id', 'level', 'content'))
        self._create_table('tags', {
            'test_id': 'INTEGER NOT NULL REFERENCES tests',
            'content': 'TEXT NOT NULL'
        }, ('test_id', 'content'))
        self._create_table('arguments', {
            'keyword_id': 'INTEGER NOT NULL REFERENCES keywords',
            'content': 'TEXT NOT NULL'
        }, ('keyword_id', 'content'))

    def _create_table(self, table_name, columns, unique_columns=()):
        definitions = ['id INTEGER PRIMARY KEY']
        for column_name, properties in columns.items():
            definitions.append('%s %s' % (column_name, properties))
        if unique_columns:
            unique_column_names = ', '.join(unique_columns)
            definitions.append('CONSTRAINT unique_%s UNIQUE (%s)' % (
                table_name, unique_column_names)
            )
        sql_statement = 'CREATE TABLE IF NOT EXISTS %s (%s)' % (table_name, ', '.join(definitions))
        self._connection.execute(sql_statement)
