from os.path import exists
from sys import argv

from dbbot.reader.reader_options import ReaderOptions


class WriterOptions(ReaderOptions):

    @property
    def output_file_path(self):
        return self._target_file

    def _get_validated_options(self):
        self._parser.set_usage('%prog [options] outfile')
        if len(argv) < 2:
            self._exit_with_help()
        options, target_files = super(WriterOptions, self)._get_validated_options()
        self._target_file = target_files.pop()
        if not exists(options.db_file_path):
            self._parser.error('database "%s" does not exists' % options.db_file_path)
        return options, self._target_file

    def _check_files(self, files):
        if not files:
            self._parser.error('output file not given')
        for path in files:
            open(path, 'a').close()