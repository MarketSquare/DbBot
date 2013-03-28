#!/usr/bin/env python

import sys
import sqlite3
from os.path import exists
from datetime import datetime
from optparse import OptionParser
from robot.result import ExecutionResult


DEFAULT_DB_NAME = "results.db"

class DbBot(object):
    def __init__(self):
        self._config = ConfigurationParser()
        self._parser = RobotOutputParser(self._config.include_keywords, self._output_verbose)
        database = ":memory:" if self._config.dry_run else self._config.db_file_path
        self._db = RobotDatabase(database, self._output_verbose)

    def run(self):
        try:
            all_test_run_results = self._results_to_dict()
            self._db.dicts_to_sql(all_test_run_results)
            self._db.commit()
        except Exception, message:
            sys.stderr.write('Error: %s\n\n' % message)
            exit(1)
        finally:
            self._db.close()

    def _results_to_dict(self):
        return [self._parser.xml_to_dict(xml_file) for xml_file in self._config.file_paths]

    def _output_verbose(self, message, header):
        if self._config.be_verbose:
            sys.stdout.write(' %-8s |   %s\n' % (header, message))


class ConfigurationParser(object):
    def __init__(self):
        self._parser = OptionParser()
        self._add_parser_options()
        self._options = self._get_validated_options()

    @property
    def file_paths(self):
        return self._options.file_paths

    @property
    def db_file_path(self):
        return self._options.db_file_path

    @property
    def be_verbose(self):
        return self._options.verbose

    @property
    def dry_run(self):
        return self._options.dry_run

    @property
    def include_keywords(self):
        return self._options.include_keywords

    def _add_parser_options(self):
        def files_args_parser(option, opt_str, _, parser):
            values = []
            for arg in parser.rargs:
                if arg[:2] == '--' and len(arg) > 2:
                    break
                if arg[:1] == '-' and len(arg) > 1:
                    break
                values.append(arg)
            del parser.rargs[:len(values)]
            setattr(parser.values, option.dest, values)

        self._parser.add_option('-v', '--verbose',
            action='store_true',
            dest='verbose',
            help='print information about execution '
        )
        self._parser.add_option('-d', '--dry-run',
            action='store_true',
            dest='dry_run',
            help='don\'t save anything into database'
        )
        self._parser.add_option('-k', '--also-keywords',
            action='store_true',
            dest='include_keywords',
            help='include suites\' and tests\' keywords'
        )
        self._parser.add_option('-b', '--database',
            dest='db_file_path',
            default=DEFAULT_DB_NAME,
            help='path to the sqlite3 database to save to',
        )
        self._parser.add_option('-f', '--files',
            action='callback',
            callback=files_args_parser,
            dest='file_paths',
            help='one or more output.xml files to save to db'
        )

    def _get_validated_options(self):
        if len(sys.argv) < 2:
            self._exit_with_help()
        options, args = self._parser.parse_args()
        if args:
            self._exit_with_help()
        if options.file_paths is None or len(options.file_paths) < 1:
            self._parser.error('at least one input file is required')
        for file_path in options.file_paths:
            if not exists(file_path):
                self._parser.error('file "%s" not exists' % file_path)
        return options

    def _exit_with_help(self):
        self._parser.print_help()
        exit(1)


class RobotOutputParser(object):
    def __init__(self, include_keywords, callback_verbose=None):
        self._include_keywords = include_keywords
        self._callback_verbose = callback_verbose

    def verbose(self, message=''):
        self._callback_verbose(message, 'Parser')

    def xml_to_dict(self, xml_file):
        self.verbose('- Parsing "%s"' % xml_file)
        test_run = ExecutionResult(xml_file)
        return {
            'source_file': test_run.source,
            'generator': test_run.generator,
            'statistics': self.parse_statistics(test_run.statistics),
            'errors': self._parse_messages(test_run.errors.messages),
            'suites': self._parse_suites(test_run.suite)
        }

    def parse_statistics(self, statistics):
        self.verbose('`--> Parsing test run statistics')
        return [
            self.total_statistics(statistics),
            self.critical_statistics(statistics),
            self.tag_statistics(statistics),
            self.suite_statistics(statistics)
        ]

    def total_statistics(self, statistics):
        self.verbose('  `--> Parsing total statistics')
        return {
            'name': 'total', 'stats': self._get_parsed_stat(statistics.total.all)
        }

    def critical_statistics(self, statistics):
        self.verbose('  `--> Parsing critical statistics')
        return {
            'name': 'critical', 'stats': self._get_parsed_stat(statistics.total.critical)
        }

    def tag_statistics(self, statistics):
        self.verbose('  `--> Parsing tag statistics')
        return {
            'name': 'tag', 'stats': [self._get_parsed_stat(tag) for tag in statistics.tags.tags.values()]
        }

    def suite_statistics(self, statistics):
        self.verbose('  `--> Parsing suite statistics')
        return {
            'name': 'suite', 'stats': [self._get_parsed_stat(suite.stat) for suite in statistics.suite.suites]
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
        self.verbose('`--> Parsing suite: %s' % subsuite.name)
        return {
            'xml_id': subsuite.id,
            'name': subsuite.name,
            'source': subsuite.source,
            'doc': subsuite.doc,
            'start_time': self._format_timestamp(subsuite.starttime),
            'end_time': self._format_timestamp(subsuite.endtime),
            'tests': self._parse_tests(subsuite.tests),
            'suites': self._parse_suites(subsuite),
            'keywords': self._parse_keywords(subsuite.keywords)
        }

    def _parse_tests(self, tests):
        return [self._get_parsed_test(test) for test in tests]

    def _get_parsed_test(self, test):
        self.verbose('  `--> Parsing test: %s' % test.name)
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
        if self._include_keywords:
            return [self._get_parsed_keyword(keyword) for keyword in keywords]
        else:
            return []

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
    def __init__(self, db_file_path, callback_verbose=None):
        self._callback_verbose = callback_verbose

        db_is_new = not exists(db_file_path)
        self._connection = self._connect(db_file_path)
        self._set_db_settings()

        if db_is_new:
            self._init_schema()

    def verbose(self, message=''):
        self._callback_verbose(message, 'Database')

    def close(self):
        self.verbose('- Closing database connection')
        self._connection.close()

    def commit(self):
        self.verbose('- Committing changes into database')
        self._connection.commit()

    def dicts_to_sql(self, dictionaries):
        self.verbose('- Mapping test run results to SQL')
        self._insert_all_elements('test_runs', dictionaries)

    def _connect(self, db_file_path):
        self.verbose('- Establishing database connection')
        return sqlite3.connect(db_file_path)

    def _set_db_settings(self):
        self._push('PRAGMA main.page_size=4096')
        self._push('PRAGMA main.cache_size=10000')
        self._push('PRAGMA main.synchronous=NORMAL')
        self._push('PRAGMA main.journal_mode=WAL')

    def _init_schema(self):
        self.verbose('- Initializing database schema')
        self._push('''CREATE TABLE test_runs (
                        id INTEGER PRIMARY KEY,
                        source_file TEXT NOT NULL,
                        generator TEXT NOT NULL
                    )''')

        self._push('''CREATE TABLE statistics (
                        id INTEGER PRIMARY KEY,
                        test_run_id INTEGER NOT NULL REFERENCES test_runs,
                        name TEXT NOT NULL
                    )''')

        self._push('''CREATE TABLE stats (
                        id INTEGER PRIMARY KEY,
                        statistic_id INTEGER NOT NULL REFERENCES statistics,
                        name TEXT NOT NULL,
                        elapsed INTEGER NOT NULL,
                        failed INTEGER NOT NULL,
                        passed INTEGER NOT NULL
                    )''')

        self._push('''CREATE TABLE suites (
                        id INTEGER PRIMARY KEY,
                        test_run_id INTEGER REFERENCES test_runs,
                        suite_id INTEGER REFERENCES suites,
                        xml_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        source TEXT NOT NULL,
                        doc TEXT NOT NULL,
                        start_time DATETIME NOT NULL,
                        end_time DATETIME NOT NULL
                    )''')

        self._push('''CREATE TABLE tests (
                        id INTEGER PRIMARY KEY,
                        suite_id INTEGER NOT NULL REFERENCES suites,
                        xml_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        timeout TEXT NOT NULL,
                        doc TEXT NOT NULL,
                        status TEXT NOT NULL
                    )''')

        self._push('''CREATE TABLE keywords (
                        id INTEGER PRIMARY KEY,
                        test_id INTEGER REFERENCES tests,
                        keyword_id INTEGER REFERENCES keywords,
                        suite_id INTEGER REFERENCES suites,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        timeout TEXT NOT NULL,
                        doc TEXT NOT NULL,
                        status TEXT NOT NULL
                    )''')

        self._push('''CREATE TABLE messages (
                        id INTEGER PRIMARY KEY,
                        keyword_id INTEGER NOT NULL REFERENCES keywords,
                        level TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        content TEXT NOT NULL
                    )''')

        self._push('''CREATE TABLE errors (
                        id INTEGER PRIMARY KEY,
                        test_run_id INTEGER NOT NULL REFERENCES test_runs,
                        level TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        content TEXT NOT NULL
                    )''')

        self._push('''CREATE TABLE tags (
                        id INTEGER PRIMARY KEY,
                        test_id INTEGER NOT NULL REFERENCES tests,
                        content TEXT NOT NULL
                    )''')

        self._push('''CREATE TABLE arguments (
                        id INTEGER PRIMARY KEY,
                        keyword_id INTEGER NOT NULL REFERENCES keywords,
                        content TEXT NOT NULL
                    )''')

        self._push('''CREATE INDEX test_run_index ON statistics(test_run_id)''')
        self._push('''CREATE INDEX statistics_index ON stats(statistic_id)''')
        self._push('''CREATE INDEX suite_test_run_index ON suites(test_run_id)''')
        self._push('''CREATE INDEX suite_index ON suites(suite_id)''')
        self._push('''CREATE INDEX test_suite_index ON tests(suite_id)''')
        self._push('''CREATE INDEX keyword_test_index ON keywords(test_id)''')
        self._push('''CREATE INDEX keyword_suite_index ON keywords(suite_id)''')
        self._push('''CREATE INDEX keyword_keyword_index ON keywords(keyword_id)''')
        self._push('''CREATE INDEX message_keyword_index ON messages(keyword_id)''')
        self._push('''CREATE INDEX error_test_run_index ON errors(test_run_id)''')
        self._push('''CREATE INDEX tag_test_index ON tags(test_id)''')
        self._push('''CREATE INDEX argument_keyword_index ON arguments(keyword_id)''')


    def _push(self, sql_statement, values=[]):
        cursor = self._connection.execute(sql_statement, values)
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
        parent_reference = ('%s_id' % db_table_name[:-1], last_inserted_row_id)
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
        column_names = ','.join(keys)
        value_placeholders = ','.join(['?'] * len(keys))
        return 'INSERT INTO %s(%s) VALUES (%s)' % (db_table_name, column_names, value_placeholders)


if __name__ == '__main__':
    DbBot().run()
