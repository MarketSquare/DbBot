dbbot
=====

This script inserts the Robot Framework test run results (output.xml files) into a sqlite database.

Usage: dbbot [options]

Options:

Short           | Long                    | Description
--------------- |-------------------------| ------------------------------------------
-v              | --verbose               | be verbose about the operation
-b DB_FILE_PATH | --database=DB_FILE_PATH | path to the sqlite3 database for test run results
-d              | --dry-run               | do everything except store results into disk
-k              | --also-keywords         | parse also suites' and tests' keywords
-f              | --files                 | one or more Robot output.xml files
