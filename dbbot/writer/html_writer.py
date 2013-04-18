class HtmlWriter(object):
    def __init__(self, db, be_verbose=False):
        self._logger = Logger('HtmlWriter') if be_verbose else None
        self._db = db

    def _verbose(self, message):
        if self._logger:
            self._logger(message)

    def write(self):
        for suite in self._db.failed_suites():
            print "SUITE: %i times: %s (%s)" % (suite['count'], suite['name'], suite['source'])
            for test in self._db.failed_tests_for_suite(suite['id']):
                print " `--> TEST: %i times: %s" % (test['count'], test['name'])
                for keyword in self._db.failed_keywords_for_test(test['id']):
                    print "   `--> KEYWORD: %i times: %s" % (keyword['count'], keyword['name'])
