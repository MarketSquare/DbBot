from sys import argv
from os.path import exists

from dbbot import CommandLineOptions


class ReaderOptions(CommandLineOptions):
    @property
    def file_paths(self):
        return self._options.file_paths

    @property
    def dry_run(self):
        return self._options.dry_run

    @property
    def include_keywords(self):
        return self._options.include_keywords

    def _add_parser_options(self):
        CommandLineOptions._add_parser_options(self)
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
        self._parser.add_option('-f', '--files',
            action='callback',
            callback=files_args_parser,
            dest='file_paths',
            help='one or more output.xml files to save to db'
        )

    def _get_validated_options(self):
        if len(argv) < 2:
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
