from sys import stdout


class Logger(object):

    def __init__(self, header, output):
        self._header = header
        self._output = output

    def __call__(self, message):
        if self._output:
            self._output.write(' %-8s |   %s\n' % (self._header, message))
