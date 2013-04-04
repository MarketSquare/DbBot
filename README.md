dbbot
=====

This command line script inserts the test run results (in output.xml files) into a sqlite3 database.

Usage: dbbot [options]

Options:
’’
Short           | Long                    | Description
--------------- |:-----------------------:| -----------------------------------------:
-h              | --help                  | show this help message and exit
-v              | --verbose               | print information about execution
-d              | --dry-run               | don't save anything into database
-k              | --also-keywords         | include suites' and tests' keywords
-b DB_FILE_PATH | --database=DB_FILE_PATH | path to the sqlite3 database to save to
-f              | --files                 | one or more output.xml files to save to db
