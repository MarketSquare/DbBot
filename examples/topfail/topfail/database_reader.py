import sqlite3

from dbbot import RobotDatabase


class DatabaseReader(RobotDatabase):

    def __init__(self, db_file_path):
        super(DatabaseReader, self).__init__(db_file_path, None)
        self._connection.row_factory = sqlite3.Row

    def most_failed_suites(self):
        sql_statement = '''
            SELECT count() as count, suites.id, suites.name, suites.source
            FROM suites, suite_status
            WHERE suites.id == suite_status.suite_id AND
            suite_status.status == "FAIL"
            GROUP BY suites.source
        '''
        return self._fetch_by(sql_statement)

    def most_failed_tests(self):
        sql_statement = '''
            SELECT count() as count, tests.id, tests.name, tests.suite_id
            FROM tests, test_status
            WHERE tests.id == test_status.test_id AND
            test_status.status == "FAIL"
            GROUP BY tests.name, tests.suite_id
        '''
        return self._fetch_by(sql_statement)

    def most_failed_keywords(self):
        sql_statement = '''
            SELECT count() as count, keywords.name, keywords.type
            FROM keywords, keyword_status
            WHERE keywords.id == keyword_status.keyword_id AND
            keyword_status.status == "FAIL"
            GROUP BY keywords.name, keywords.type
        '''
        return self._fetch_by(sql_statement)

    def failed_tests_for_suite(self, suite_id):
        sql_statement = '''
            SELECT count() as count, tests.id, tests.name, tests.suite_id
            FROM tests, test_status
            WHERE tests.id == test_status.test_id AND
            tests.suite_id == ? AND
            test_status.status == "FAIL"
            GROUP BY tests.name
        '''
        return self._fetch_by(sql_statement, [suite_id])

    def failed_keywords_for_test(self, test_id):
        sql_statement = '''
            SELECT count() as count, keywords.name, keywords.type
            FROM keywords, keyword_status
            WHERE keywords.id == keyword_status.keyword_id AND
            keywords.test_id == ? AND
            keyword_status.status == "FAIL"
            GROUP BY keywords.name, keywords.type
        '''
        return self._fetch_by(sql_statement, [test_id])

    def _fetch_by(self, sql_statement, values=[]):
        return self._connection.execute(sql_statement, values).fetchall()

