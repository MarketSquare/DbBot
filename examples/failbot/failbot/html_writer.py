import os
from string import Template
from xml.sax.saxutils import escape

from dbbot import Logger


class HtmlWriter(object):
    template_path = os.path.abspath(__file__ + '../../../templates')

    # escape() only takes care of &, < and >
    additional_html_escapes = {
        '"': "&quot;",
        "'": "&apos;"
    }

    def __init__(self, db, output_file_path, verbose_stream):
        self._verbose = Logger('HTML', verbose_stream)
        self._db = db
        self._output_file_path = output_file_path
        self._init_layouts()

    def _init_layouts(self):
        self._verbose('- Loading HTML templates')
        self._full_layout = self._read_template('layout.html')
        self._table_layout = self._read_template('table.html')
        self._row_layout = self._read_template('row.html')

    def _read_template(self, filename):
        with open(os.path.join(self.template_path, filename), 'r') as file:
            content = file.read()
        return Template(content)

    def produce(self):
        self._verbose('- Producing summaries from database')
        output_html = self._full_layout.substitute({
            'most_failed_suites': self._table_of_most_failed_suites(),
            'most_failed_tests': self._table_of_most_failed_tests(),
            'most_failed_keywords': self._table_of_most_failed_keywords()
        })
        self._write_file(self._output_file_path, output_html)

    def _write_file(self, filename, content):
        self._verbose('- Writing %s' % filename)
        with open(filename, 'w') as file:
            file.write(content)

    def _table_of_most_failed_suites(self):
        return self._format_table(self._db.most_failed_suites())

    def _table_of_most_failed_tests(self):
        return self._format_table(self._db.most_failed_tests())

    def _table_of_most_failed_keywords(self):
        return self._format_table(self._db.most_failed_keywords())

    def _format_table(self, rows):
        return self._table_layout.substitute({
            'rows': ''.join([self._format_row(row) for row in rows])
        })

    def _format_row(self, item):
        return self._row_layout.substitute({
            'name': self._escape(item['name']),
            'count': item['count']
        })

    def _escape(self, text):
        return escape(text, self.additional_html_escapes)
