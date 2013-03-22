#!/usr/bin/env python

import sys
import optparse
import sqlite3
from os.path import exists
from datetime import datetime
from robot.result import ExecutionResult


def main():
    try:
        config = ConfigurationParser()
        output_xml_file = ExecutionResult(config.file_path)
        output_parser = RobotOutputParser(output_xml_file)
        test_run_results = output_parser.results_to_dict()
    except Exception, message:
        _output_error_and_exit('Error: %s\n\n' % message)
    db = RobotDatabase(config.db_file_path)
    try:
        db.dict_to_sql(test_run_results)
        db.commit()
    except Exception, message:
        _output_error_and_exit('Database error: %s\n\n' % message)
    finally:
        db.close()

def _output_error_and_exit(message=None):
    sys.stderr.write(message)
    exit(1)


class ConfigurationParser(object):
    def __init__(self):
        self.parser = optparse.OptionParser()
        self._add_parser_options()
        self.options = self._get_validated_options()

    @property
    def file_path(self):
        return self.options.file_path

    @property
    def db_file_path(self):
        return self.options.db_file_path

    def _add_parser_options(self):
        self.parser.add_option('--file', dest='file_path')
        self.parser.add_option('--db', dest='db_file_path', default='results.db')

    def _get_validated_options(self):
        if len(sys.argv) < 2:
            self._exit_with_help()
        options, args = self.parser.parse_args()
        if args:
            self._exit_with_help()
        if not exists(options.file_path):
            raise Exception('File "%s" not exists.' % options.file_path)
        return options

    def _exit_with_help(self):
        self.parser.print_help()
        exit(1)


class RobotOutputParser(object):
    def __init__(self, output_file):
        self.test_run = output_file

    def results_to_dict(self):
        return {
            'source_file': self.test_run.source,
            'generator': self.test_run.generator,
            'statistics': self.parse_statistics(),
            'errors': self._parse_messages(self.test_run.errors.messages),
            'suites': self._parse_suites(self.test_run.suite)
        }

    def parse_statistics(self):
        return [
            self.total_statistics(),
            self.critical_statistics(),
            self.tag_statistics(),
            self.suite_statistics()
        ]

    def total_statistics(self):
        return {
            'name': 'total', 'stats': self._get_parsed_stat(self.test_run.statistics.total.all)
        }

    def critical_statistics(self):
        return {
            'name': 'critical', 'stats': self._get_parsed_stat(self.test_run.statistics.total.critical)
        }

    def tag_statistics(self):
        return {
            'name': 'tag', 'stats': [self._get_parsed_stat(tag) for tag in self.test_run.statistics.tags.tags.values()]
        }

    def suite_statistics(self):
        return {
            'name': 'suite', 'stats': [self._get_parsed_stat(suite.stat) for suite in self.test_run.statistics.suite.suites]
        }

    def _get_parsed_stat(self, stat):
        return {
            'name': stat.name,
            'elapsed': stat.elapsed,
            'failed': stat.failed,
            'passed': stat.passed
        }

    def _parse_suites(self, suite):
        return [self._get_parsed_suite(subsuite) for subsuite in suite.suites]

    def _get_parsed_suite(self, subsuite):
        return {
            'xml_id': subsuite.id,
            'name': subsuite.name,
            'source': subsuite.source,
            'doc': subsuite.doc,
            'start_time': self._format_timestamp(subsuite.starttime),
            'end_time': self._format_timestamp(subsuite.endtime),
            'keywords': self._parse_keywords(subsuite.keywords),
            'tests': self._parse_tests(subsuite.tests),
            'suites': self._parse_suites(subsuite)
        }

    def _parse_tests(self, tests):
        return [self._get_parsed_test(test) for test in tests]

    def _get_parsed_test(self, test):
        return {
            'xml_id': test.id,
            'name': test.name,
            'timeout': test.timeout,
            'doc': test.doc,
            'status': test.status,
            'tags': self._parse_tags(test.tags),
            'keywords': self._parse_keywords(test.keywords)
        }

    def _parse_keywords(self, keywords):
        return [self._get_parsed_keyword(keyword) for keyword in keywords]

    def _get_parsed_keyword(self, keyword):
        return {
            'name': keyword.name,
            'type': keyword.type,
            'timeout': keyword.timeout,
            'doc': keyword.doc,
            'status': keyword.status,
            'messages': self._parse_messages(keyword.messages),
            'arguments': self._parse_arguments(keyword.args),
            'keywords': self._parse_keywords(keyword.keywords)
        }

    def _parse_arguments(self, args):
        return [self._get_parsed_content(arg) for arg in args]

    def _parse_tags(self, tags):
        return [self._get_parsed_content(tag) for tag in tags]

    def _get_parsed_content(self, content):
        return { 'content': content }

    def _parse_messages(self, messages):
        return [self._get_parsed_message(message) for message in messages]

    def _get_parsed_message(self, message):
        return {
            'level': message.level,
            'timestamp': self._format_timestamp(message.timestamp),
            'content': message.message
        }

    def _format_timestamp(self, timestamp):
        return str(datetime.strptime(timestamp.split('.')[0], '%Y%m%d %H:%M:%S'))


class RobotDatabase(object):
    def __init__(self, db_file_path):
        self.connection = sqlite3.connect(db_file_path)
        self._init_schema()

    def _init_schema(self):
        self._push('''CREATE TABLE IF NOT EXISTS test_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_file TEXT NOT NULL,
                        generator TEXT NOT NULL
                    )''')

        self._push('''CREATE TABLE IF NOT EXISTS statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        FOREIGN KEY(test_run_id) REFERENCES test_runs(id)
                    )''')

        self._push('''CREATE TABLE IF NOT EXISTS stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        statistic_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        elapsed INTEGER NOT NULL,
                        failed INTEGER NOT NULL,
                        passed INTEGER NOT NULL,
                        FOREIGN KEY(statistic_id) REFERENCES statistics(id)
                    )''')

        self._push('''CREATE TABLE IF NOT EXISTS suites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_id INTEGER,
                        suite_id INTEGER,
                        xml_id TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        source TEXT NOT NULL,
                        doc TEXT NOT NULL,
                        start_time DATETIME NOT NULL,
                        end_time DATETIME NOT NULL,
                        FOREIGN KEY(test_run_id) REFERENCES test_runs(id),
                        FOREIGN KEY(suite_id) REFERENCES suites(id)
                    )''')

        self._push('''CREATE TABLE IF NOT EXISTS tests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        suite_id INTEGER NOT NULL,
                        xml_id TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        timeout TEXT NOT NULL,
                        doc TEXT NOT NULL,
                        status TEXT NOT NULL,
                        FOREIGN KEY(suite_id) REFERENCES suites(id)
                    )''')

        self._push('''CREATE TABLE IF NOT EXISTS keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id INTEGER,
                        keyword_id INTEGER,
                        suite_id INTEGER,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        timeout TEXT NOT NULL,
                        doc TEXT NOT NULL,
                        status TEXT NOT NULL,
                        FOREIGN KEY(test_id) REFERENCES tests(id),
                        FOREIGN KEY(keyword_id) REFERENCES keywords(id),
                        FOREIGN KEY(suite_id) REFERENCES suites(id)
                    )''')

        self._push('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword_id INTEGER NOT NULL,
                        level TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        content TEXT NOT NULL,
                        FOREIGN KEY(keyword_id) REFERENCES keywords(id)
                    )''')

        self._push('''CREATE TABLE IF NOT EXISTS errors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_id INTEGER NOT NULL,
                        level TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        content TEXT NOT NULL,
                        FOREIGN KEY(test_run_id) REFERENCES test_runs(id)
                    )''')

        self._push('''CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        FOREIGN KEY(test_id) REFERENCES tests(id)
                    )''')

        self._push('''CREATE TABLE IF NOT EXISTS arguments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        FOREIGN KEY(keyword_id) REFERENCES keywords(id)
                    )''')

    def close(self):
        self.connection.close()

    def commit(self):
        self.connection.commit()

    def dict_to_sql(self, dictionary):
        self._insert_all_elements('test_runs', dictionary)

    def _push(self, sql_statement, values=[]):
        cursor = self.connection.execute(sql_statement, values)
        return cursor.lastrowid

    def _insert_all_elements(self, db_table_name, elements, parent_reference=None):
        if type(elements) is not list:
            elements = [elements]
        [self._insert_element_as_row(db_table_name, element, parent_reference) for element in elements]

    def _insert_element_as_row(self, db_table_name, element, parent_reference=None):
        if not parent_reference is None:
            element[parent_reference[0]] = parent_reference[1]
        keys, values = self._get_simple_types(element)
        query = self._make_insert_query(db_table_name, keys)
        last_inserted_row_id = self._push(query, values)
        parent_reference = ("%s_id" % db_table_name[:-1], last_inserted_row_id)
        for key in list(set(element.keys()) - set(keys)):
            self._insert_all_elements(key, element[key], parent_reference)

    def _get_simple_types(self, dictionary):
        keys, values = [], []
        for key, value in dictionary.iteritems():
            if not isinstance(value, (list, dict)):
                keys.append(key)
                values.append(value)
        return keys, values

    def _make_insert_query(self, db_table_name, keys):
        column_names = ",".join(keys)
        value_placeholders = ','.join(['?'] * len(keys))
        return 'INSERT INTO %s(%s) VALUES (%s)' % (db_table_name, column_names, value_placeholders)


if __name__ == '__main__':
    main()
