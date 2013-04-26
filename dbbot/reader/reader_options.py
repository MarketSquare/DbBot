from os.path import exists
from sys import argv

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
        super(ReaderOptions, self)._add_parser_options()
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
            help='do everything except store results into disk'
        )
        self._parser.add_option('-k', '--also-keywords',
            action='store_true',
            dest='include_keywords',
            help='parse also suites\' and tests\' keywords'
        )
        self._parser.add_option('-f', '--files',
            action='callback',
            callback=files_args_parser,
            dest='file_paths',
            help='one or more Robot output.xml files'
        )

    def _get_validated_options(self):
        if len(argv) < 2:
            self._exit_with_help()
        options = super(ReaderOptions, self)._get_validated_options()
        if options.file_paths is None or len(options.file_paths) < 1:
            self._parser.error('at least one input file is required')
        for file_path in options.file_paths:
            if not exists(file_path):
                self._parser.error('file %s not exists' % file_path)
        return options
