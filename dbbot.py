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
        'suites': parse_suites(results.suite),
    }

def parse_statistics(statistics):
    return {
        'total': get_total_statistics(statistics),
        'tag': get_tag_statistics(statistics),
        'suite': get_suite_statistics(statistics),
    }

def get_total_statistics(statistics):
    return {
        'all': _get_total_stat(statistics.total.all),
        'critical': _get_total_stat(statistics.total.critical),
    }

def _get_total_stat(stat):
    return {
        'name': stat.name,
        'elapsed': stat.elapsed,
        'passed': stat.passed,
        'failed': stat.failed,
    }

def get_tag_statistics(statistics):
    return [_get_parsed_tag_stat(tag) for tag in statistics.tags.tags.values()]

def _get_parsed_tag_stat(stat):
    return {
        'name': stat.name,
        'doc': stat.doc,
        'non_critical': stat.non_critical,
        'elapsed': stat.elapsed,
        'failed': stat.failed,
        'critical': stat.critical,
        'combined': stat.combined,
        'passed': stat.passed,
    }

def get_suite_statistics(statistics):
    return [_get_parsed_suite_stat(suite.stat) for suite in statistics.suite.suites]

def _get_parsed_suite_stat(stat):
    return {
        'name': stat.name,
        'elapsed': stat.elapsed,
        'failed': stat.failed,
        'passed': stat.passed,
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
        'suites': parse_suites(subsuite),
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
        'keywords': parse_keywords(test.keywords),
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
    return [_get_parsed_arg(arg) for arg in args]

def _get_parsed_arg(arg):
    return {
        'content': arg,
    }

def parse_tags(tags):
    return [_get_parsed_tag(tag) for tag in tags]

def _get_parsed_tag(tag):
    return {
        'content': tag,
    }

def _get_parsed_message(message):
    return {
        'level': message.level,
        'timestamp': _format_timestamp(message.timestamp),
        'content': message.message,
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

    def insert(self, dictionary):
        test_run_id = self._insert_test_run(dictionary)
        self._insert_suites(dictionary['suites'], test_run_id)
        self._insert_test_run_statistics(dictionary['statistics'], test_run_id)
        self._insert_test_run_errors(dictionary['errors'], test_run_id)

    def close(self):
        self.connection.close()

    def _enable_foreign_keys(self):
        self._execute('PRAGMA foreign_keys = on')
        self.connection.commit()

    def _init_schema(self):
        self._execute('''CREATE TABLE IF NOT EXISTS test_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_file TEXT,
                        generator TEXT,
                        errors_id INTEGER,
                        statistics_id INTEGER,
                        suite_id INTEGER,
                        FOREIGN KEY(suite_id) REFERENCES suites(id)
                    )''')

        # has 0-n messages
        self._execute('''CREATE TABLE IF NOT EXISTS test_run_errors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_id INTEGER,
                        FOREIGN KEY(test_run_id) REFERENCES test_runs(id)
                    )''')

        # has 0-n stats (tag)
        # has 0-n stats (suite)
        self._execute('''CREATE TABLE IF NOT EXISTS test_run_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_id INTEGER,
                        FOREIGN KEY(test_run_id) REFERENCES test_runs(id)
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_statistics_id INTEGER,
                        name TEXT,
                        links TEXT,
                        doc TEXT,
                        non_critical INTEGER,
                        elapsed INTEGER,
                        failed INTEGER,
                        critical INTEGER,
                        combined TEXT,
                        passed INTEGER,
                        FOREIGN KEY(test_run_statistics_id) REFERENCES test_run_statistics(id)
                    )''')

        # has 0-n suites (as sub-suites)
        self._execute('''CREATE TABLE IF NOT EXISTS suites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_id INTEGER,
                        setup_keyword_id INTEGER,
                        teardown_keyword_id INTEGER,
                        name TEXT,
                        source TEXT,
                        doc TEXT,
                        start_time DATETIME,
                        end_time DATETIME,
                        FOREIGN KEY(setup_keyword_id) REFERENCES keywords(id),
                        FOREIGN KEY(teardown_keyword_id) REFERENCES keywords(id)
                    )''')

        # has 0-n tags
        # has 0-n keywords
        # has 0-n messages
        self._execute('''CREATE TABLE IF NOT EXISTS tests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        suite_id INTEGER,
                        name TEXT,
                        timeout TEXT,
                        doc TEXT,
                        status TEXT,
                        FOREIGN KEY(suite_id) REFERENCES suites(id)
                    )''')

        # parent_id can be suite_id, test_id or keyword_id
        # has 0-n messages
        # has 0-n keywords (as sub-keywords)
        self._execute('''CREATE TABLE  IF NOT EXISTS keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_id INTEGER,
                        name TEXT,
                        type TEXT,
                        timeout TEXT,
                        doc TEXT,
                        status TEXT,
                        argument_id INTEGER,
                        FOREIGN KEY(argument_id) REFERENCES arguments(id)
                    )''')

        # parent_id: test_id, test_run_errors_id or keyword_id
        self._execute('''CREATE TABLE  IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_id INTEGER,
                        level TEXT,
                        timestamp DATETIME,
                        content TEXT
                    )''')

        self._execute('''CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id INTEGER,
                        content TEXT,
                        FOREIGN KEY(test_id) REFERENCES tests(id)
                    )''')

        self._execute('''CREATE TABLE  IF NOT EXISTS arguments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword_id INTEGER,
                        content TEXT,
                        FOREIGN KEY(keyword_id) REFERENCES keywords(id)
                    )''')

    def _execute(self, statement, values=[]):
        cursor = self.connection.cursor()
        cursor.execute(statement, values)
        self.connection.commit()
        return cursor.lastrowid

    def _insert_messages(self, messages, parent_id):
        for message in messages:
            parent_values = self._remove_children(message)
            parent_values['parent_id'] = parent_id
            self._insert_dictionary('messages', parent_values)

    def _insert_test_run_errors(self, errors, test_run_id):
        parent_values = {
            'test_run_id': test_run_id
        }
        test_run_errors_id = self._insert_dictionary('test_run_errors', parent_values)
        self._insert_messages(errors, test_run_errors_id)

    def _insert_arguments(self, arguments, keyword_id):
        for argument in arguments:
            parent_values = self._remove_children(argument)
            parent_values['keyword_id'] = keyword_id
            self._insert_dictionary('arguments', parent_values)

    def _insert_test_run_statistics(self, statistics, test_run_id):
        parent_values = {
            'test_run_id': test_run_id
        }
        test_runs_statistics_id = self._insert_dictionary('test_run_statistics', parent_values)
        self._insert_stat(statistics['total']['all'], test_runs_statistics_id)
        self._insert_stat(statistics['total']['critical'], test_runs_statistics_id)
        for stat in statistics['tag']:
            self._insert_stat(stat, test_runs_statistics_id)
        for stat in statistics['suite']:
            self._insert_stat(stat, test_runs_statistics_id)

    def _insert_stat(self, stat, test_run_statistics_id):
        stat['test_run_statistics_id'] = test_run_statistics_id
        self._insert_dictionary('stats', stat)

    def _insert_test_run(self, test_run):
        parent_values = self._remove_children(test_run)
        return self._insert_dictionary('test_runs', parent_values)

    def _insert_suites(self, suites, parent_id):
        for suite in suites:
            parent_values = self._remove_children(suite)
            parent_values['parent_id'] = parent_id
            suite_id = self._insert_dictionary('suites', parent_values)
            self._insert_keywords(suite['keywords'], suite_id)
            self._insert_tests(suite['tests'], suite_id)
            self._insert_suites(suite['suites'], suite_id)

    def _insert_keywords(self, keywords, parent_id):
        for keyword in keywords:
            parent_values = self._remove_children(keyword)
            parent_values['parent_id'] = parent_id
            keyword_id = self._insert_dictionary('keywords', parent_values)
            self._insert_messages(keyword['messages'], keyword_id)
            self._insert_arguments(keyword['arguments'], keyword_id)
            self._insert_keywords(keyword['keywords'], keyword_id)

    def _insert_tests(self, tests, suite_id):
        for test in tests:
            parent_values = self._remove_children(test)
            parent_values['suite_id'] = suite_id
            test_id = self._insert_dictionary('tests', parent_values)
            self._insert_tags(test['tags'], test_id)
            self._insert_keywords(test['keywords'], test_id)

    def _insert_tags(self, tags, test_id):
        for tag in tags:
            parent_values = self._remove_children(tag)
            parent_values['test_id'] = test_id
            self._insert_dictionary('tags', parent_values)

    def _insert_dictionary(self, tablename, data):
        fields = data.keys()
        values = data.values()
        fieldlist = ",".join(fields)
        placeholderlist = ','.join(['?'] * len(fields))
        query = 'INSERT INTO %s(%s) VALUES (%s)' % (tablename, fieldlist, placeholderlist)
        return self._execute(query, values)

    def _remove_children(self, dictionary):
        stripped_dictionary = deepcopy(dictionary)
        for key in stripped_dictionary.keys():
            if isinstance(stripped_dictionary[key], (list, dict)):
                stripped_dictionary.pop(key)
        return stripped_dictionary


if __name__ == '__main__':
    main()
