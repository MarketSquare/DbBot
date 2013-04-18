from os.path import exists
from sys import argv

from dbbot import CommandLineOptions


DEFAULT_HTML_FILE_NAME = 'index.html'

class WriterOptions(CommandLineOptions):
    @property
    def output_file_path(self):
        return self._options.output_file_path

    def _add_parser_options(self):
        super(WriterOptions, self)._add_parser_options()
        self._parser.add_option('-o', '--output',
            dest='output_file_path',
            default=DEFAULT_HTML_FILE_NAME,
            help='output test run summary html file',
        )

    def _get_validated_options(self):
        options, args = self._parser.parse_args()
        if args:
            self._exit_with_help()
        if not exists(options.db_file_path):
            self._parser.error('database %s not exists' % options.db_file_path)
        return options
