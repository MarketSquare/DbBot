from optparse import OptionParser


DEFAULT_DB_NAME = 'robot_results.db'

class CommandLineOptions(object):
    def __init__(self):
        self._parser = OptionParser()
        self._add_parser_options()
        self._options = self._get_validated_options()

    @property
    def db_file_path(self):
        return self._options.db_file_path

    @property
    def be_verbose(self):
        return self._options.verbose

    def _add_parser_options(self):
        self._parser.add_option('-v', '--verbose',
            action='store_true',
            dest='verbose',
            help='print information about the execution '
        )
        self._parser.add_option('-b', '--database',
            dest='db_file_path',
            default=DEFAULT_DB_NAME,
            help='sqlite3 database containing the results',
        )

    def _exit_with_help(self):
        self._parser.print_help()
        exit(1)
