from string import Template

from dbbot import Logger


TEMPLATE_PATH = '../data'

class HtmlWriter(object):

    def __init__(self, db, output_file_path):
        self._db = db
        self._output_file_path = output_file_path
        self._load_layouts()

    def _load_layouts(self):
        self._full_layout = Template(open('%s/layout.html' % TEMPLATE_PATH, 'r').read())
        self._table_layout = Template(open('%s/table.html' % TEMPLATE_PATH, 'r').read())
        self._row_layout = Template(open('%s/row.html' % TEMPLATE_PATH, 'r').read())

    def write(self):
        output = self._full_layout.substitute({
            'most_failed_suites': self._most_failed_suites(),
            'most_failed_tests': self._most_failed_tests(),
            'most_failed_keywords': self._most_failed_keywords()
        })
        with open(self._output_file_path, 'w') as file:
            file.write(output)

    def _most_failed_suites(self):
        rows = [self._format_row(suite) for suite in self._db.most_failed_suites()]
        return self._format_table('most failed suites', rows)

    def _most_failed_tests(self):
        rows = [self._format_row(test) for test in self._db.most_failed_tests()]
        return self._format_table('most failed tests', rows)

    def _most_failed_keywords(self):
        rows = [self._format_row(keyword) for keyword in self._db.most_failed_keywords()]
        return self._format_table('most failed keywords', rows)

    def _format_table(self, title, rows):
        return self._table_layout.substitute({
            'table_title': title,
            'rows': ''.join(rows)
        })

    def _format_row(self, item):
        return self._row_layout.substitute({
            'name': item['name'],
            'count': item['count']
        })
