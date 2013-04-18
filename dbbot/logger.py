from sys import stdout


class Logger(object):
    def __init__(self, header, output=stdout):
        self._output = output
        self._header = header

    def __call__(self, message):
        self._output.write(' %-8s |   %s\n' % (self._header, message))
