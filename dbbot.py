#!/usr/bin/env python

import sys
import optparse
import sqlite3
from os.path import exists
from datetime import datetime
from robot.result import ExecutionResult

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

    # TODO: more detailed exceptions
    try:
        db = RobotDatabase(options)
        db.insert_into_db(results_dictionary)
    except Exception, message:
        output_error_message(message)
    finally:
        db.close()


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
        'links': stat.links,
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
        'suite_id': stat.id,
        'name': stat.name,
        'elapsed': stat.elapsed,
        'failed': stat.failed,
        'passed': stat.passed,
    }

def parse_suites(suite):
    return [_get_parsed_suite(subsuite) for subsuite in suite.suites]

def _get_parsed_suite(subsuite):
    return {
        'id': subsuite.id,
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
        'id': test.id,
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
        self.sql_statements = []
        self.connection = sqlite3.connect(options.db_file_path)
        self._enable_foreign_keys()
        self._init_tables()

    def _enable_foreign_keys(self):
        self._push('pragma foreign_keys = on')
        self._commit()

    def _init_tables(self):
        self._push('''CREATE TABLE  IF NOT EXISTS test_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_file TEXT,
                        generator TEXT,
                        errors_id INTEGER,
                        statistics_id INTEGER,
                        suite_id INTEGER NOT NULL
                    )''')

        # has 0-n messages
        self._push('''CREATE TABLE  IF NOT EXISTS test_run_errors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_id INTEGER NOT NULL
                    )''')

        # has 0-n stats (tag)
        # has 0-n stats (suite)
        self._push('''CREATE TABLE  IF NOT EXISTS test_run_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_id INTEGER NOT NULL,
                        stats_all_id INTEGER,
                        stats_critical_id INTEGER
                    )''')

        self._push('''CREATE TABLE  IF NOT EXISTS stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_run_statistics_id INTEGER NOT NULL,
                        suite_id INTEGER,
                        name TEXT,
                        links TEXT,
                        doc TEXT,
                        non_critical INTEGER,
                        elapsed INTEGER,
                        failed INTEGER,
                        critical INTEGER,
                        combined TEXT,
                        passed INTEGER
                    )''')

        # has 0-n suites (as sub-suites)
        self._push('''CREATE TABLE  IF NOT EXISTS suites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_id INTEGER,
                        setup_keyword_id INTEGER,
                        teardown_keyword_id INTEGER,
                        name TEXT,
                        source TEXT,
                        doc TEXT,
                        start_time DATETIME,
                        end_time DATETIME
                    )''')

        # has 0-n tags
        # has 0-n keywords
        # has 0-n messages
        self._push('''CREATE TABLE  IF NOT EXISTS tests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        suite_id INTEGER NOT NULL,
                        name TEXT,
                        timeout TEXT,
                        doc TEXT,
                        status TEXT
                    )''')

        # parent_id can be suite_id, test_id or keyword_id
        # has 0-n messages
        # has 0-n keywords (as sub-keywords)
        self._push('''CREATE TABLE  IF NOT EXISTS keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_id INTEGER NOT NULL,
                        name TEXT,
                        type TEXT,
                        timeout TEXT,
                        doc TEXT,
                        status TEXT,
                        argument_id INTEGER
                    )''')

        # parent_id: test_id, test_run_errors_id or keyword_id
        self._push('''CREATE TABLE  IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_id INTEGER NOT NULL,
                        level TEXT,
                        timestamp DATETIME,
                        content TEXT
                    )''')

        self._push('''CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id INTEGER NOT NULL,
                        content TEXT
                    )''')

        self._push('''CREATE TABLE  IF NOT EXISTS arguments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id INTEGER NOT NULL,
                        content TEXT
                    )''')

        self._commit()

    def _push(self, *sql_statements):
        self.sql_statements.extend(sql_statements)

    def _commit(self):
        cursor = self.connection.cursor()
        for statement in self.sql_statements:
            if isinstance(statement, basestring):
                cursor = cursor.execute(statement)
            else:
                cursor = cursor.execute(*statement)
            self.connection.commit()
        self.sql_statements = []

    def insert_into_db(self, dictionary):
        pprint(dictionary)

    def close(self):
        self.connection.close()


if __name__ == '__main__':
    main()
