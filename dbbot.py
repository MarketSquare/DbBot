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
        database = ":memory:" if self._config.dry_run else self._config.db_file_path
        self._db = RobotDatabase(database, self._output_verbose)
        self._parser = RobotOutputParser(self._config.include_keywords, self._db, self._output_verbose)

    def run(self):
        try:
            [self._parser.xml_to_dict(xml_file) for xml_file in self._config.file_paths]
            self._db.commit()
        except Exception, message:
            sys.stderr.write('Error: %s\n\n' % message)
            exit(1)
        finally:
            self._db.close()

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
    def __init__(self, include_keywords, db, callback_verbose=None):
        self._include_keywords = include_keywords
        self._callback_verbose = callback_verbose
        self._db = db

    def verbose(self, message=''):
        self._callback_verbose(message, 'Parser')

    def xml_to_dict(self, xml_file):
        self.verbose('- Parsing "%s"' % xml_file)
        test_run = ExecutionResult(xml_file)
        test_run_id = self._db._push('''
            INSERT INTO test_runs (source_file, generator) VALUES (?,?)''',
            (test_run.source, test_run.generator)
        )
        self._parse_statistics(test_run.statistics, test_run_id)
        self._parse_messages(test_run.errors.messages, test_run_id)
        self._parse_suites(test_run.suite, test_run_id)

    def _parse_statistics(self, statistics, test_run_id):
        self.verbose('`--> Parsing test run statistics')
        self._total_statistics(statistics, test_run_id)
        self._critical_statistics(statistics, test_run_id)
        self._tag_statistics(statistics, test_run_id)
        self._suite_statistics(statistics, test_run_id)

    def _total_statistics(self, statistics, test_run_id):
        self.verbose('  `--> Parsing total statistics')
        statistics_id = self._db._push('''
            INSERT INTO statistics (test_run_id, name) VALUES (?,?)''',
            (test_run_id, 'total')
        )
        self._parse_stats(statistics.total.all, statistics_id)

    def _critical_statistics(self, statistics, test_run_id):
        self.verbose('  `--> Parsing critical statistics')
        statistics_id = self._db._push('''
            INSERT INTO statistics (test_run_id, name) VALUES (?,?)''',
            (test_run_id, 'critical')
        )
        self._parse_stats(statistics.total.critical, statistics_id)

    def _tag_statistics(self, statistics, test_run_id):
        self.verbose('  `--> Parsing tag statistics')
        statistics_id = self._db._push('''
            INSERT INTO statistics (test_run_id, name) VALUES (?,?)''',
            (test_run_id, 'tag')
        )
        [self._parse_stats(tag, statistics_id) for tag in statistics.tags.tags.values()]

    def _suite_statistics(self, statistics, test_run_id):
        self.verbose('  `--> Parsing suite statistics')
        statistics_id = self._db._push('''
            INSERT INTO statistics (test_run_id, name) VALUES (?,?)''',
            (test_run_id, 'suite')
        )
        [self._parse_stats(suite.stat, statistics_id) for suite in statistics.suite.suites]

    def _parse_stats(self, stat, statistics_id):
        self._db._push('''
            INSERT INTO stats (statistics_id, name, elapsed, failed, passed)
            VALUES (?,?,?,?,?)''',
            (statistics_id, stat.name, stat.elapsed, stat.failed, stat.passed)
        )

    def _parse_suites(self, suite, test_run_id, suite_id=None):
        [self._parse_suite(subsuite, test_run_id, suite_id) for subsuite in suite.suites]

    def _parse_suite(self, suite, test_run_id, suite_id):
        self.verbose('`--> Parsing suite: %s' % suite.name)
        suite_id = self._db._push('''
            INSERT INTO suites (test_run_id, suite_id, xml_id, name, source,
            doc, start_time, end_time) VALUES (?,?,?,?,?,?,?,?)''',
            (test_run_id, suite_id, suite.id, suite.name, suite.source,
            suite.doc, self._format_timestamp(suite.starttime),
            self._format_timestamp(suite.endtime))
        )
        self._parse_suites(suite, None, suite_id)
        self._parse_tests(suite.tests, suite_id)
        self._parse_keywords(suite.keywords, suite_id, None, None)

    def _parse_tests(self, tests, suite_id):
        [self._parse_test(test, suite_id) for test in tests]

    def _parse_test(self, test, suite_id):
        self.verbose('  `--> Parsing test: %s' % test.name)
        test_id = self._db._push('''
            INSERT INTO tests (suite_id, xml_id, name, timeout, doc, status)
            VALUES (?,?,?,?,?,?)''',
            (suite_id, test.id, test.name, test.timeout, test.doc, test.status)
        )
        self._parse_tags(test.tags, test_id)
        self._parse_keywords(test.keywords, None, test_id, None)

    def _parse_keywords(self, keywords, suite_id, test_id, keyword_id):
        if self._include_keywords:
            [self._parse_keyword(keyword, suite_id, test_id, keyword_id) for keyword in keywords]

    def _parse_keyword(self, keyword, suite_id, test_id, keyword_id):
        keyword_id = self._db._push('''
            INSERT INTO keywords (suite_id, test_id, keyword_id, name, type,
            timeout, doc, status) VALUES (?,?,?,?,?,?,?,?)''',
            (suite_id, test_id, keyword_id, keyword.name, keyword.type,
            keyword.timeout, keyword.doc, keyword.status)
        )
        self._parse_messages(keyword.messages, keyword_id)
        self._parse_arguments(keyword.args, keyword_id)
        self._parse_keywords(keyword.keywords, None, None, keyword_id)

    def _parse_tags(self, tags, test_id):
        self._db._push_many('''
            INSERT INTO tags (test_id, content) VALUES (?,?)''',
            [(test_id, tag) for tag in tags]
        )

    def _parse_arguments(self, args, keyword_id):
        self._db._push_many('''
            INSERT INTO arguments (keyword_id, content) VALUES (?,?)''',
            [(keyword_id, arg) for arg in args]
        )

    def _parse_errors(self, error, test_run_id):
        self._db._push_many('''
            INSERT INTO messages (test_run_id, level, timestamp, content)
            VALUES (?,?,?,?)''',
            [(test_run_id, error.level, self._format_timestamp(error.timestamp),
            error.message) for error in errors]
        )

    def _parse_messages(self, messages, keyword_id):
        self._db._push_many('''
            INSERT INTO messages (keyword_id, level, timestamp, content)
            VALUES (?,?,?,?)''',
            [(keyword_id, message.level, self._format_timestamp(message.timestamp),
            message.message) for message in messages]
        )

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
                        statistics_id INTEGER NOT NULL REFERENCES statistics,
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
        self._push('''CREATE INDEX statistics_index ON stats(statistics_id)''')
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

    def _push(self, sql_statement, values=()):
        cursor = self._connection.execute(sql_statement, values)
        return cursor.lastrowid

    def _push_many(self, sql_statement, values=[]):
        self._connection.executemany(sql_statement, values)

if __name__ == '__main__':
    DbBot().run()
