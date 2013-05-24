import os
import glob
from datetime import datetime
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
        self._init_templates()

    def _init_templates(self):
        self._verbose('- Loading HTML templates')
        for filename in self.template_files():
            attr_name = "_%s" % filename.split('.')[0]
            setattr(type(self), attr_name, self._read_template(filename))

    def template_files(self):
        return filter(lambda x: x.endswith('.html'), os.listdir(self.template_path))

    def _read_template(self, filename):
        with open(os.path.join(self.template_path, filename), 'r') as file:
            content = file.read()
        return Template(content)

    def produce(self):
        self._verbose('- Producing summaries from database')
        output_html = self._layout.substitute({
            'output_files': self._output_tables()
        })
        self._write_file(self._output_file_path, output_html)

    def _write_file(self, filename, content):
        self._verbose('- Writing %s' % filename)
        with open(filename, 'w') as file:
            file.write(content)

    def _output_tables(self):
        output_files = self._db.source_files()
        return ''.join([self._output_table(o) for o in output_files])

    def _output_table(self, output):
        source_file = output['source_file']
        return self._output_files.substitute({
            'output_file': source_file,
            'results_table': self._test_table(source_file)
        })

    def _test_table(self, source_file):
        return self._table.substitute({
            'test_runs': self._test_runs_for_source(source_file),
            'test_cases': self._test_cases_for_source(source_file)
        })

    def _test_runs_for_source(self, source_file):
        test_runs = self._db.test_runs_for_source_file(source_file)
        return ''.join([self._format_test_run(t) for t in test_runs])

    def _format_test_run(self, test_run):
        return self._test_runs.substitute({
            'test_run_id': test_run['id'],
            'test_run_at': self._format_date(test_run['finished_at'])
        })

    def _test_cases_for_source(self, source_file):
        test_cases = self._db.test_cases_for_source_file(source_file)
        return ''.join([self._format_test_case(t) for t in test_cases])

    def _format_test_case(self, test_case):
        return self._test_cases.substitute({
            'test_case_id': test_case['xml_id'],
            'test_case_name': test_case['name'],
            'test_case_status': self._test_case_statuses(test_case['id'])
        })

    def _test_case_statuses(self, test_id):
        test_statuses = self._db.test_results_for_test(test_id)
        return ''.join([self._format_test_status(t) for t in test_statuses])

    def _format_test_status(self, test_status):
        return self._test_case_status.substitute({
            'status': test_status['status'].lower()
        })

    def _format_date(self, timestamp):
        date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        return datetime.strftime(date, '%d.%m %H:%M')

    def _escape(self, text):
        return escape(text, self.additional_html_escapes)
