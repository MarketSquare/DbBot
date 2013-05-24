import sqlite3

from dbbot import RobotDatabase


class DatabaseReader(RobotDatabase):

    def __init__(self, db_file_path, verbose_stream):
        super(DatabaseReader, self).__init__(db_file_path, verbose_stream)
        self._connection.row_factory = sqlite3.Row

    def source_files(self):
        sql_statement = '''
            SELECT DISTINCT source_file
            FROM test_runs
        '''
        return self._fetch_by(sql_statement)

    def test_runs_for_source_file(self, source_file):
        sql_statement = '''
            SELECT id, finished_at
            FROM test_runs
            WHERE source_file == ?
        '''
        return self._fetch_by(sql_statement, [source_file])

    def test_cases_for_source_file(self, source_file):
        sql_statement = '''
            SELECT tests.id, tests.xml_id, tests.name
            FROM tests, test_status
            WHERE test_status.test_run_id in (
                SELECT id FROM test_runs WHERE
                test_runs.source_file == ?
            )
        '''
        return self._fetch_by(sql_statement, [source_file])

    def test_results_for_test(self, test_id):
        sql_statement = '''
            SELECT test_status.status
            FROM test_status
            WHERE test_status.test_id == ?
        '''
        return self._fetch_by(sql_statement, [test_id])

    def _fetch_by(self, sql_statement, values=[]):
        return self._connection.execute(sql_statement, values).fetchall()

