#!/usr/bin/env python

import sys
import sqlite3
from os.path import exists
from datetime import datetime
from optparse import OptionParser
from robot.result import ExecutionResult


DEFAULT_DB_NAME = 'results.db'

class DbBot(object):
    def __init__(self):
        self._config = ConfigurationParser()
        database = ':memory:' if self._config.dry_run else self._config.db_file_path
        self._db = RobotDatabase(database, self._output_verbose)
        self._parser = RobotOutputParser(
            self._config.include_keywords,
            self._db,
            self._output_verbose
        )

    def run(self):
        try:
            for xml_file in self._config.file_paths:
                self._parser.xml_to_db(xml_file)
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
                self._parser.error('file %s not exists' % file_path)
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

    def xml_to_db(self, xml_file):
        self.verbose('- Parsing %s' % xml_file)
        test_run = ExecutionResult(xml_file)
        test_run_id = self._db.insert_row('test_runs', {
            'source_file': test_run.source,
            'generator': test_run.generator
        })
        self._parse_errors(test_run.errors.messages, test_run_id)
        self._parse_statistics(test_run.statistics, test_run_id)
        self._parse_suites(test_run.suite)

    def _parse_errors(self, errors, test_run_id):
        self._db.insert_many('errors', ('test_run_id', 'level', 'timestamp', 'content'),
            [(test_run_id, error.level, self._format_timestamp(error.timestamp), error.message)
            for error in errors]
        )

    def _parse_statistics(self, statistics, test_run_id):
        self.verbose('`--> Parsing test run statistics')
        self._total_statistics(statistics, test_run_id)
        self._critical_statistics(statistics, test_run_id)
        self._tag_statistics(statistics, test_run_id)
        self._suite_statistics(statistics, test_run_id)

    def _total_statistics(self, statistics, test_run_id):
        self.verbose('  `--> Parsing total statistics')
        statistics_id = self._db.insert_row('statistics', {
            'test_run_id': test_run_id,
            'name': 'total'
        })
        self._parse_stats(statistics.total.all, statistics_id)

    def _critical_statistics(self, statistics, test_run_id):
        self.verbose('  `--> Parsing critical statistics')
        statistics_id = self._db.insert_row('statistics', {
            'test_run_id': test_run_id,
            'name': 'critical'
        })
        self._parse_stats(statistics.total.critical, statistics_id)

    def _tag_statistics(self, statistics, test_run_id):
        self.verbose('  `--> Parsing tag statistics')
        statistics_id = self._db.insert_row('statistics', {
            'test_run_id': test_run_id,
            'name': 'tag'
        })
        [self._parse_stats(tag, statistics_id) for tag in statistics.tags.tags.values()]

    def _suite_statistics(self, statistics, test_run_id):
        self.verbose('  `--> Parsing suite statistics')
        statistics_id = self._db.insert_row('statistics', {
            'test_run_id': test_run_id,
            'name': 'suite'
        })
        [self._parse_stats(suite.stat, statistics_id) for suite in statistics.suite.suites]

    def _parse_stats(self, stat, statistics_id):
        self._db.insert_row('stats', {
            'statistics_id': statistics_id,
            'name': stat.name,
            'elapsed': stat.elapsed,
            'failed': stat.failed,
            'passed': stat.passed
        })

    def _parse_suites(self, suite, parent_suite_id=None):
        [self._parse_suite(subsuite, parent_suite_id) for subsuite in suite.suites]

    def _parse_suite(self, suite, parent_suite_id):
        self.verbose('`--> Parsing suite: %s' % suite.name)
        try:
            suite_id = self._db.insert_row('suites', {
                'suite_id': parent_suite_id,
                'xml_id': suite.id,
                'name': suite.name,
                'source': suite.source,
                'doc': suite.doc
            })
        except sqlite3.IntegrityError:
            suite_id = self._db.fetch_id('suites', {
                'name': suite.name,
                'source': suite.source
            })
        self._parse_suites(suite, suite_id)
        self._parse_tests(suite.tests, suite_id)
        self._parse_keywords(suite.keywords, suite_id, None)

    def _parse_tests(self, tests, suite_id):
        [self._parse_test(test, suite_id) for test in tests]

    def _parse_test(self, test, suite_id):
        self.verbose('  `--> Parsing test: %s' % test.name)
        try:
            test_id = self._db.insert_row('tests', {
                'suite_id': suite_id,
                'xml_id': test.id,
                'name': test.name,
                'timeout': test.timeout,
                'doc': test.doc
            })
        except sqlite3.IntegrityError:
            test_id = self._db.fetch_id('tests', {
                'suite_id': suite_id,
                'name': test.name
            })
        self._parse_tags(test.tags, test_id)
        self._parse_keywords(test.keywords, None, test_id)

    def _parse_tags(self, tags, test_id):
        self._db.insert_many('tags', ('test_id', 'content'),
            [(test_id, tag) for tag in tags]
        )

    def _parse_keywords(self, keywords, suite_id, test_id, keyword_id=None):
        if self._include_keywords:
            [self._parse_keyword(keyword, suite_id, test_id, keyword_id)
            for keyword in keywords]

    def _parse_keyword(self, keyword, suite_id, test_id, keyword_id):
        try:
            keyword_id = self._db.insert_row('keywords', {
                'suite_id': suite_id,
                'test_id': test_id,
                'keyword_id': keyword_id,
                'name': keyword.name,
                'type': keyword.type,
                'timeout': keyword.timeout,
                'doc': keyword.doc
            })
        except sqlite3.IntegrityError:
            keyword_id = self._db.fetch_id('keywords', {
                'name': keyword.name,
                'type': keyword.type
            })
        self._parse_messages(keyword.messages, keyword_id)
        self._parse_arguments(keyword.args, keyword_id)
        self._parse_keywords(keyword.keywords, None, None, keyword_id)

    def _parse_messages(self, messages, keyword_id):
        self._db.insert_many('messages', ('keyword_id', 'level', 'timestamp', 'content'),
            [(keyword_id, message.level, self._format_timestamp(message.timestamp),
            message.message) for message in messages]
        )

    def _parse_arguments(self, args, keyword_id):
        self._db.insert_many('arguments', ('keyword_id', 'content'),
            [(keyword_id, arg) for arg in args]
        )

    def _format_timestamp(self, timestamp):
        return str(datetime.strptime(timestamp.split('.')[0], '%Y%m%d %H:%M:%S'))


class RobotDatabase(object):
    def __init__(self, db_file_path, callback_verbose=None):
        self._callback_verbose = callback_verbose
        db_is_new = not exists(db_file_path)
        self._connection = self._connect(db_file_path)
        self._configure()
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

    def fetch_id(self, table_name, criteria):
        sql_statement = 'SELECT id FROM %s WHERE ' % table_name
        sql_statement += ' AND '.join('%s=?' % key for key in criteria.keys())
        return self._connection.execute(sql_statement, criteria.values()).fetchone()[0]

    def insert_row(self, table_name, criteria):
        column_names = ','.join(criteria.keys())
        placeholders = ','.join('?' * len(criteria))
        sql_statement = 'INSERT OR ABORT INTO %s (%s) VALUES (%s)' % (
            table_name, column_names, placeholders
        )
        cursor = self._connection.execute(sql_statement, criteria.values())
        return cursor.lastrowid

    def insert_many(self, table_name, columns, values):
        column_names = ','.join(columns)
        placeholders = ','.join('?' * len(columns))
        sql_statement = 'INSERT OR IGNORE INTO %s (%s) VALUES (%s)' % (
            table_name, column_names, placeholders
        )
        self._connection.executemany(sql_statement, values)

    def _connect(self, db_file_path):
        self.verbose('- Establishing database connection')
        return sqlite3.connect(db_file_path)

    def _configure(self):
        self._set('page_size', 4096)
        self._set('cache_size', 10000)
        self._set('synchronous', 'NORMAL')
        self._set('journal_mode', 'WAL')

    def _set(self, name, value):
        self.verbose('- Configuring database')
        sql_statement = 'PRAGMA %s=%s' % (name, value)
        self._connection.execute(sql_statement)

    def _init_schema(self):
        self.verbose('- Initializing database schema')
        self._create_table('test_runs', {
            'source_file': 'TEXT NOT NULL',
            'generator': 'TEXT NOT NULL'
        })
        self._create_table('statistics', {
            'test_run_id': 'INTEGER NOT NULL REFERENCES test_runs',
            'name': 'TEXT NOT NULL'
        })
        self._create_table('stats', {
            'statistics_id': 'INTEGER NOT NULL REFERENCES statistics',
            'name': 'TEXT NOT NULL',
            'elapsed': 'INTEGER NOT NULL',
            'failed': 'INTEGER NOT NULL',
            'passed': 'INTEGER NOT NULL'
        })
        self._create_table('suites', {
            'test_run_id': 'INTEGER REFERENCES test_runs',
            'suite_id': 'INTEGER REFERENCES suites',
            'xml_id': 'TEXT NOT NULL',
            'name': 'TEXT NOT NULL',
            'source': 'TEXT NOT NULL',
            'doc': 'TEXT NOT NULL'
        }, ('name', 'source'))
        self._create_table('tests', {
            'suite_id': 'INTEGER NOT NULL REFERENCES suites',
            'xml_id': 'TEXT NOT NULL',
            'name': 'TEXT NOT NULL',
            'timeout': 'TEXT NOT NULL',
            'doc': 'TEXT NOT NULL'
        }, ('suite_id', 'name'))
        self._create_table('keywords', {
            'suite_id': 'INTEGER REFERENCES suites',
            'test_id': 'INTEGER REFERENCES tests',
            'keyword_id': 'INTEGER REFERENCES keywords',
            'name': 'TEXT NOT NULL',
            'type': 'TEXT NOT NULL',
            'timeout': 'TEXT NOT NULL',
            'doc': 'TEXT NOT NULL'
        }, ('name', 'type'))
        self._create_table('messages', {
            'keyword_id': 'INTEGER NOT NULL REFERENCES keywords',
            'level': 'TEXT NOT NULL',
            'timestamp': 'DATETIME NOT NULL',
            'content': 'TEXT NOT NULL'
        }, ('keyword_id', 'level', 'content'))
        self._create_table('errors', {
            'test_run_id': 'INTEGER NOT NULL REFERENCES test_runs',
            'level': 'TEXT NOT NULL',
            'timestamp': 'DATETIME NOT NULL',
            'content': 'TEXT NOT NULL'
        }, ('test_run_id', 'level', 'content'))
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
        sql_statement = 'CREATE TABLE %s (%s)' % (table_name, ', '.join(definitions))
        self._connection.execute(sql_statement)

if __name__ == '__main__':
    DbBot().run()
