#!/usr/bin/env python

import sys
import optparse
import sqlite3
from datetime import datetime
from os.path import abspath, exists, join
from xml.etree import ElementTree


def main():
    parser = _get_option_parser()
    options = _get_validated_options(parser)
    xml_tree = _get_xml_tree(options, parser)
    root_attributes = _get_root_attributes(xml_tree)
    db = RobotDatabase(options)
    db.push(('INSERT INTO test_run (generated_at, generator) VALUES (?, ?)', root_attributes))
    db.commit()

def _exit_with_help(parser, message=None):
    if message:
        sys.stderr.write('Error: %s\n\n' % message)
    parser.print_help()
    exit(1)

def _get_option_parser():
    parser = optparse.OptionParser()
    parser.add_option('--file', dest='file_path')
    parser.add_option('--db', dest='db_file_path', default='results.db')
    return parser

def _get_xml_tree(options, parser):
    try:
        xml_tree = ElementTree.parse(options.file_path)
    except ElementTree.ParseError:
        _exit_with_help(parser, 'Invalid XML file')
    return xml_tree

def _get_formatted_timestamp(root_element):
    generated_at = root_element.get('generated').split('.')[0]
    return datetime.strptime(generated_at, '%Y%m%d %H:%M:%S')

def _get_root_attributes(xml_tree):
    root_element = xml_tree.getroot()
    return (
        _get_formatted_timestamp(root_element),
        root_element.get('generator')
    )

def _get_validated_options(parser):
    if len(sys.argv) < 2:
        _exit_with_help(parser)
    options, args = parser.parse_args()
    if args:
        _exit_with_help(parser)
    if not exists(options.file_path):
        _exit_with_help(parser, 'File not found')
    return options


class RobotDatabase(object):

    def __init__(self, options):
        self.sql_statements = []
        self.options = options
        self._init_tables()

    def _init_tables(self):
        self.push(
            '''CREATE TABLE if not exists test_run (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                    generated_at TEXT,
                                                    generator TEXT)''')
        self.commit()

    def push(self, *sql_statements):
        for statement in sql_statements:
            self.sql_statements.append(statement)

    def commit(self):
        connection = sqlite3.connect(self.options.db_file_path)
        cursor = connection.cursor()
        for statement in self.sql_statements:
            if isinstance(statement, basestring):
                cursor.execute(statement)
            else:
                cursor.execute(*statement)
            connection.commit()
        self.sql_statements = []
        connection.close()

if __name__ == '__main__':
    main()
