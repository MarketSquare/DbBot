from optparse import OptionParser
from os.path import exists


DEFAULT_DB_NAME = 'robot_results.db'

class ReaderOptions(object):

    def __init__(self):
        self._parser = OptionParser()
        self._add_parser_options()
        self._options, self._files = self._get_validated_options()

    def _add_parser_options(self):
        options = [
            ('-d', '--dry-run', {'action': 'store_true',
                                 'default': False,
                                 'dest': 'dry_run',
                                 'help': 'do everything except store results into disk'}),

            ('-k', '--also-keywords', {'action':'store_true',
                                       'default': False,
                                       'dest': 'include_keywords',
                                       'help': 'parse also suites\' and tests\' keywords'}),

            ('-v', '--verbose', {'action': 'store_true',
                                 'default': False,
                                 'dest': 'be_verbose',
                                 'help': 'be verbose about the operation'}),

            ('-b', '--database', {'dest': 'db_file_path',
                                  'default': DEFAULT_DB_NAME,
                                  'help': 'path to the SQLite database for test run results'})
        ]
        for option in options:
            self._parser.add_option(option[0], option[1], **option[2])

    def _get_validated_options(self):
        options, files = self._parser.parse_args()
        self._check_files(files)
        return options, files

    def _check_files(self, files):
        if not files or len(files) < 1:
            self._parser.error('at least one input file is required')
        for file_path in files:
            if not exists(file_path):
                self._parser.error('file "%s" does not exist' % file_path)

    def _exit_with_help(self):
        self._parser.print_help()
        exit(1)

    @property
    def db_file_path(self):
        return self._options.db_file_path

    @property
    def be_verbose(self):
        return self._options.be_verbose

    @property
    def file_paths(self):
        return self._files

    @property
    def dry_run(self):
        return self._options.dry_run

    @property
    def include_keywords(self):
        return self._options.include_keywords
