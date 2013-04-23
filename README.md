dbbot
=====

DbBot is a Python script used to serialize Robot Framework produced
test run results, i.e. output.xml files into a SQLite database.

The script takes one or more output.xml files as input, initializes the
database schema, creates respective insert statements and finally inserts the results
into the database (robot_results.db by default, can be specified using -b or --database).

Both the test data (names and paths) and test statistics (how many did pass or fail,
possible errors occurred, how long it took to run, etc.) related to suites and test cases
are stored. Optionally keywords can be stored (by -k or --also-keywords flag) but
this is not the default behavior as it might take a while for massive test runs.


Use cases
---------
One of the common needs is to get a report of the most commonly failing suites,
tests and keywords. DbBot comes with an executable example named 'topfail',
bundled in 'examples/topfail/bin/topfail'.

Topfail is used to produce an html summary based on the test data serialized
into the dbbot database. Feel free to adjust (the very basic) html templates
to your needs.

Another potential use case would be to build a script that generates an html
summary of the most time-consuming tests, keywords etc.


Requirements
------------

* Python 2.6 or newer installed
* Robot Framework 2.7 or newer installed

Tested and verified on Python 2.7.4 and Robot Framework 2.7.7


Usage
-----
There is an executable Python script named 'dbbot' under directory 'bin'.

Run the script from command-line: dbbot [options]

Valid command-line options are:

Short format    | Long format             | Description
--------------- |-------------------------| ------------------------------------------
-v              | --verbose               | be verbose about the operation
-b DB_FILE_PATH | --database=DB_FILE_PATH | path to the sqlite3 database for test run results
-d              | --dry-run               | do everything except store results into disk
-k              | --also-keywords         | parse also suites' and tests' keywords
-f              | --files                 | one or more Robot output.xml files

On Windows environments you might need to rename the script to have '.py' file extension.


Usage examples
--------------
TODO


Directory structure
-------------------

Directory | Description
----------|------------
atests    | Robot Framework powered acceptance tests for DbBot. Also contains test fixtures.
bin       | Contains the executables, mainly 'dbbot'. You may want to append this directory to your PATH.
dbbot     | Contains the packages used by dbbot. You may want to append this directory to your PYTHONPATH if you are developing scripts that inherit the abstract classes in package 'dbbot'
doc       | Mainly technical documentation about the database schema.
examples  | Examples that are using the dbbot created database and inhering from the 'dbbot' package.



