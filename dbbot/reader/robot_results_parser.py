#  Copyright 2013-2014 Nokia Solutions and Networks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from __future__ import with_statement
from datetime import datetime
from hashlib import sha1
from robot.api import ExecutionResult
from sqlite3 import IntegrityError


from dbbot import Logger


class RobotResultsParser(object):

    def __init__(self, include_keywords, db, verbose_stream):
        self._verbose = Logger('Parser', verbose_stream)
        self._include_keywords = include_keywords
        self._db = db

    def xml_to_db(self, xml_file):
        self._verbose('- Parsing %s' % xml_file)
        test_run = ExecutionResult(xml_file, include_keywords=self._include_keywords)
        hash = self._hash(xml_file)
        try:
            test_run_id = self._db.insert('test_runs', {
                'hash': hash,
                'imported_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
                'source_file': test_run.source,
                'started_at': self._format_robot_timestamp(test_run.suite.starttime),
                'finished_at': self._format_robot_timestamp(test_run.suite.endtime)
            })
        except IntegrityError:
            test_run_id = self._db.fetch_id('test_runs', {
                'source_file': test_run.source,
                'started_at': self._format_robot_timestamp(test_run.suite.starttime),
                'finished_at': self._format_robot_timestamp(test_run.suite.endtime)
            })
        self._parse_errors(test_run.errors.messages, test_run_id)
        self._parse_statistics(test_run.statistics, test_run_id)
        self._parse_suite(test_run.suite, test_run_id)

    def _hash(self, xml_file):
        block_size = 68157440
        hasher = sha1()
        with open(xml_file, 'rb') as f:
            chunk = f.read(block_size)
            while len(chunk) > 0:
                hasher.update(chunk)
                chunk = f.read(block_size)
        return hasher.hexdigest()

    def _parse_errors(self, errors, test_run_id):
        self._db.insert_many_or_ignore('test_run_errors',
            ('test_run_id', 'level', 'timestamp', 'content'),
            [(test_run_id, error.level, self._format_robot_timestamp(error.timestamp), error.message)
            for error in errors]
        )

    def _parse_statistics(self, statistics, test_run_id):
        self._parse_test_run_statistics(statistics.total, test_run_id)
        self._parse_tag_statistics(statistics.tags, test_run_id)

    def _parse_test_run_statistics(self, test_run_statistics, test_run_id):
        self._verbose('`--> Parsing test run statistics')
        [self._parse_test_run_stats(stat, test_run_id) for stat in test_run_statistics]

    def _parse_tag_statistics(self, tag_statistics, test_run_id):
        self._verbose('  `--> Parsing tag statistics')
        [self._parse_tag_stats(stat, test_run_id) for stat in tag_statistics.tags.values()]

    def _parse_tag_stats(self, stat, test_run_id):
        self._db.insert_or_ignore('tag_status', {
            'test_run_id': test_run_id,
            'name': stat.name,
            'critical': stat.critical,
            'elapsed': getattr(stat, 'elapsed', None),
            'failed': stat.failed,
            'passed': stat.passed
        })

    def _parse_test_run_stats(self, stat, test_run_id):
        self._db.insert_or_ignore('test_run_status', {
            'test_run_id': test_run_id,
            'name': stat.name,
            'elapsed': getattr(stat, 'elapsed', None),
            'failed': stat.failed,
            'passed': stat.passed
        })

    def _parse_suite(self, suite, test_run_id, parent_suite_id=None):
        self._verbose('`--> Parsing suite: %s' % suite.name)
        try:
            suite_id = self._db.insert('suites', {
                'suite_id': parent_suite_id,
                'xml_id': suite.id,
                'name': suite.name,
                'source': suite.source,
                'doc': suite.doc
            })
        except IntegrityError:
            suite_id = self._db.fetch_id('suites', {
                'name': suite.name,
                'source': suite.source
            })
        self._parse_suite_status(test_run_id, suite_id, suite)
        self._parse_suites(suite, test_run_id, suite_id)
        self._parse_tests(suite.tests, test_run_id, suite_id)
        self._parse_keywords(suite.keywords, test_run_id, suite_id, None)

    def _parse_suite_status(self, test_run_id, suite_id, suite):
        self._db.insert_or_ignore('suite_status', {
            'test_run_id': test_run_id,
            'suite_id': suite_id,
            'passed': suite.statistics.all.passed,
            'failed': suite.statistics.all.failed,
            'elapsed': suite.elapsedtime,
            'status': suite.status
        })

    def _parse_suites(self, suite, test_run_id, parent_suite_id):
        [self._parse_suite(subsuite, test_run_id, parent_suite_id) for subsuite in suite.suites]

    def _parse_tests(self, tests, test_run_id, suite_id):
        [self._parse_test(test, test_run_id, suite_id) for test in tests]

    def _parse_test(self, test, test_run_id, suite_id):
        self._verbose('  `--> Parsing test: %s' % test.name)
        try:
            test_id = self._db.insert('tests', {
                'suite_id': suite_id,
                'xml_id': test.id,
                'name': test.name,
                'timeout': test.timeout,
                'doc': test.doc
            })
        except IntegrityError:
            test_id = self._db.fetch_id('tests', {
                'suite_id': suite_id,
                'name': test.name
            })
        self._parse_test_status(test_run_id, test_id, test)
        self._parse_tags(test.tags, test_id)
        self._parse_keywords(test.keywords, test_run_id, None, test_id)

    def _parse_test_status(self, test_run_id, test_id, test):
        self._db.insert_or_ignore('test_status', {
            'test_run_id': test_run_id,
            'test_id': test_id,
            'status': test.status,
            'elapsed': test.elapsedtime
        })

    def _parse_tags(self, tags, test_id):
        self._db.insert_many_or_ignore('tags', ('test_id', 'content'),
            [(test_id, tag) for tag in tags]
        )

    def _parse_keywords(self, keywords, test_run_id, suite_id, test_id, keyword_id=None):
        if self._include_keywords:
            [self._parse_keyword(keyword, test_run_id, suite_id, test_id, keyword_id)
            for keyword in keywords]

    def _parse_keyword(self, keyword, test_run_id, suite_id, test_id, keyword_id):
        try:
            keyword_id = self._db.insert('keywords', {
                'suite_id': suite_id,
                'test_id': test_id,
                'keyword_id': keyword_id,
                'name': keyword.name,
                'type': keyword.type,
                'timeout': keyword.timeout,
                'doc': keyword.doc
            })
        except IntegrityError:
            keyword_id = self._db.fetch_id('keywords', {
                'name': keyword.name,
                'type': keyword.type
            })
        self._parse_keyword_status(test_run_id, keyword_id, keyword)
        self._parse_messages(keyword.messages, keyword_id)
        self._parse_arguments(keyword.args, keyword_id)
        self._parse_keywords(keyword.keywords, test_run_id, None, None, keyword_id)

    def _parse_keyword_status(self, test_run_id, keyword_id, keyword):
        self._db.insert_or_ignore('keyword_status', {
            'test_run_id': test_run_id,
            'keyword_id': keyword_id,
            'status': keyword.status,
            'elapsed': keyword.elapsedtime
        })

    def _parse_messages(self, messages, keyword_id):
        self._db.insert_many_or_ignore('messages', ('keyword_id', 'level', 'timestamp', 'content'),
            [(keyword_id, message.level, self._format_robot_timestamp(message.timestamp),
            message.message) for message in messages]
        )

    def _parse_arguments(self, args, keyword_id):
        self._db.insert_many_or_ignore('arguments', ('keyword_id', 'content'),
            [(keyword_id, arg) for arg in args]
        )

    def _format_robot_timestamp(self, timestamp):
        return datetime.strptime(timestamp, '%Y%m%d %H:%M:%S.%f')
