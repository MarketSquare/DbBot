#!/usr/bin/env python

import sys
import optparse
import sqlite3
from os.path import exists
from datetime import datetime
from robot.result import ExecutionResult
from copy import deepcopy

# -- for debugging purposes only
import json
def pprint(payload):
    print json.dumps(payload, sort_keys=True, indent=2)
# ---

def main():
    parser = _get_option_parser()
    options = _get_validated_options(parser)
    output_xml_file = ExecutionResult(options.file_path)
    results_dictionary = parse_test_run(output_xml_file)
    writer = RobotDatabase(options)
    try:
        writer.insert(results_dictionary)
    except Exception, message:
        output_error_message(message)
    finally:
        writer.close()


def parse_test_run(results):
    return {
        'source_file': results.source,
        'generator': results.generator,
        'statistics': parse_statistics(results.statistics),
        'errors': parse_messages(results.errors.messages),
        'suites': parse_suites(results.suite)
    }

def parse_statistics(statistics):
    return [
        get_total_all_statistics(statistics),
        get_total_critical_statistics(statistics),
        get_tag_statistics(statistics),
        get_suite_statistics(statistics)
    ]

def get_total_all_statistics(statistics):
    return {
        'name': 'total', 'stats': _get_parsed_stat(statistics.total.all)
    }

def get_total_critical_statistics(statistics):
    return {
        'name': 'critical', 'stats': _get_parsed_stat(statistics.total.critical)
    }

def get_tag_statistics(statistics):
    return {
        'name': 'tag', 'stats': [_get_parsed_stat(tag) for tag in statistics.tags.tags.values()]
    }

def get_suite_statistics(statistics):
    return {
        'name': 'suite', 'stats': [_get_parsed_stat(suite.stat) for suite in statistics.suite.suites]
    }

def _get_parsed_stat(stat):
    return {
        'name': stat.name,
        'elapsed': stat.elapsed,
        'failed': stat.failed,
        'passed': stat.passed
    }

def parse_suites(suite):
    return [_get_parsed_suite(subsuite) for subsuite in suite.suites]

def _get_parsed_suite(subsuite):
    return {
        'name': subsuite.name,
        'source': subsuite.source,
        'doc': subsuite.doc,
        'start_time': _format_timestamp(subsuite.starttime),
        'end_time': _format_timestamp(subsuite.endtime),
        'keywords': parse_keywords(subsuite.keywords),
        'tests': parse_tests(subsuite.tests),
        'suites': parse_suites(subsuite)
    }

def parse_tests(tests):
    return [_get_parsed_test(test) for test in tests]

def _get_parsed_test(test):
    return {
        'name': test.name,
        'timeout': test.timeout,
        'doc': test.doc,
        'status': test.status,
        'tags': parse_tags(test.tags),
        'keywords': parse_keywords(test.keywords)
    }

def parse_keywords(keywords):
    return [_get_parsed_keyword(keyword) for keyword in keywords]

def _get_parsed_keyword(keyword):
    return {
        'name': keyword.name,
        'type': keyword.type,
        'timeout': keyword.timeout,
        'doc': keyword.doc,
        'status': keyword.status,
        'messages': parse_messages(keyword.messages),
        'arguments': parse_arguments(keyword.args),
        'keywords': parse_keywords(keyword.keywords)
    }

def parse_arguments(args):
    return [_format_parsed_content(arg) for arg in args]

def parse_tags(tags):
    return [_format_parsed_content(tag) for tag in tags]

def _format_parsed_content(content):
    return { 'content': content }

def _get_parsed_message(message):
    return {
        'level': message.level,
        'timestamp': _format_timestamp(message.timestamp),
        'content': message.message
    }

def parse_messages(messages):
    return [_get_parsed_message(message) for message in messages]

def _format_timestamp(timestamp):
    return str(datetime.strptime(timestamp.split('.')[0], '%Y%m%d %H:%M:%S'))

def _get_option_parser():
    parser = optparse.OptionParser()
    parser.add_option('--file', dest='file_path')
    parser.add_option('--db', dest='db_file_path', default='results.db')
    return parser

def _get_validated_options(parser):
    if len(sys.argv) < 2:
        _exit_with_help(parser)
    options, args = parser.parse_args()
    if args:
        _exit_with_help(parser)
    if not exists(options.file_path):
        _exit_with_help(parser, 'File not found')
    return options

def _exit_with_help(parser, message=None):
    if message:
        output_error_message(message)
    parser.print_help()
    exit(1)

def output_error_message(message):
    sys.stderr.write('Error: %s\n\n' % message)


class RobotDatabase(object):
    def __init__(self, options):
        self.sql_statements = {}
        self.connection = sqlite3.connect(options.db_file_path)
        self._enable_foreign_keys()
        self._init_schema()

    def close(self):
        self.connection.close()

    def _enable_foreign_keys(self):
        self._execute('PRAGMA foreign_keys = on')
        self.connection.commit()

    def _init_schema(self):
        self._execute('''CREATE TABLE IF NOT EXISTS test_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_file TEXT,
                        generator TEXT
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_id INTEGER NOT NULL,
                        name TEXT,
                        FOREIGN KEY(test_run_id) REFERENCES test_runs(id)
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        statistic_id INTEGER NOT NULL,
                        name TEXT,
                        elapsed INTEGER,
                        failed INTEGER,
                        passed INTEGER,
                        FOREIGN KEY(statistic_id) REFERENCES statistics(id)
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS suites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_id INTEGER,
                        suite_id INTEGER,
                        name TEXT,
                        source TEXT,
                        doc TEXT,
                        start_time DATETIME,
                        end_time DATETIME,
                        FOREIGN KEY(test_run_id) REFERENCES test_runs(id),
                        FOREIGN KEY(suite_id) REFERENCES suites(id)
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS tests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        suite_id INTEGER NOT NULL,
                        name TEXT,
                        timeout TEXT,
                        doc TEXT,
                        status TEXT,
                        FOREIGN KEY(suite_id) REFERENCES suites(id)
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id INTEGER,
                        keyword_id INTEGER,
                        suite_id INTEGER,
                        name TEXT,
                        type TEXT,
                        timeout TEXT,
                        doc TEXT,
                        status TEXT,
                        FOREIGN KEY(test_id) REFERENCES tests(id),
                        FOREIGN KEY(keyword_id) REFERENCES keywords(id),
                        FOREIGN KEY(suite_id) REFERENCES suites(id)
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword_id INTEGER NOT NULL,
                        level TEXT,
                        timestamp DATETIME,
                        content TEXT,
                        FOREIGN KEY(keyword_id) REFERENCES keywords(id)
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS errors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_id INTEGER NOT NULL,
                        level TEXT,
                        timestamp DATETIME,
                        content TEXT,
                        FOREIGN KEY(test_run_id) REFERENCES test_runs(id)
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id INTEGER NOT NULL,
                        content TEXT,
                        FOREIGN KEY(test_id) REFERENCES tests(id)
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS arguments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword_id INTEGER NOT NULL,
                        content TEXT,
                        FOREIGN KEY(keyword_id) REFERENCES keywords(id)
                    )''')

    def _execute(self, statement, values=[]):
        cursor = self.connection.cursor()
        cursor.execute(statement, values)
        self.connection.commit()
        return cursor.lastrowid

    def insert(self, dictionary):
        self._insert_table('test_runs', dictionary)

    def _insert_table(self, db_table_name, items, parent_reference=None):
        if type(items) is not list:
            items = [items]
        [self._insert_row(db_table_name, item, parent_reference) for item in items]

    def _insert_row(self, db_table_name, object, parent_reference=None):
        if not parent_reference is None:
            object[parent_reference[0]] = parent_reference[1]
        keys, values = self._get_parent_values(object)
        query = self._make_insert_query(db_table_name, keys)
        last_inserted_row_id = self._execute(query, values)
        parent_reference = ("%s_id" % db_table_name[:-1], last_inserted_row_id)
        for key in list(set(object.keys()) - set(keys)):
            self._insert_table(key, object[key], parent_reference)

    def _get_parent_values(self, object):
        keys = []
        values = []
        for key, value in object.iteritems():
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
