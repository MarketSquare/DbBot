from optparse import OptionParser


class CommandLineOptions(object):
    default_db_name = 'robot_results.db'

    def __init__(self):
        self._parser = OptionParser()
        self._add_parser_options()
        self._options = self._get_validated_options()

    @property
    def db_file_path(self):
        return self._options.db_file_path

    @property
    def be_verbose(self):
        return self._options.be_verbose

    def _add_parser_options(self):
        self._parser.add_option('-v', '--verbose',
            action='store_true',
            dest='be_verbose',
            help='be verbose about the operation'
        )
        self._parser.add_option('-b', '--database',
            dest='db_file_path',
            default=self.default_db_name,
            help='path to the SQLite database for test run results'
        )

    def _get_validated_options(self):
        options, args = self._parser.parse_args()
        # if unknown are arguments given
        if args:
            self._exit_with_help()
        return options

    def _exit_with_help(self):
        self._parser.print_help()
        exit(1)
