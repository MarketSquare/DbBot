dbbot
=====

Purpose
-------
This script inserts the Robot Framework test run results (in output.xml files) into a sqlite database.


Requirements
------------

* Python 2.6 or newer installed
* Robot Framework 2.7 or newer installed

Tested and verified on Python 2.7.4 and Robot Framework 2.7.7


Usage
-----
There is an executable Python script named 'dbbot' under directory 'bin'.

Run it from command-line: dbbot [options]

Possible command-line options are:

Short           | Long                    | Description
--------------- |-------------------------| ------------------------------------------
-v              | --verbose               | be verbose about the operation
-b DB_FILE_PATH | --database=DB_FILE_PATH | path to the sqlite3 database for test run results
-d              | --dry-run               | do everything except store results into disk
-k              | --also-keywords         | parse also suites' and tests' keywords
-f              | --files                 | one or more Robot output.xml files

On Windows environments you might need to rename the script to have '.py' file extension.


Examples
--------
TODO

