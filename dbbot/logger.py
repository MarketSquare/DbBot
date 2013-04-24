from sys import stdout


class Logger(object):

    def __init__(self, header, stream):
        self._header = header
        self._stream = stream

    def __call__(self, message):
        if self._stream:
            self._stream.write(' %-8s |   %s\n' % (self._header, message))
