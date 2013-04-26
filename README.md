DbBot
=====

DbBot is a Python script to serialize Robot Framework produced test run results,
i.e. output.xml files, into a SQLite database. This way the future Robot Framework
related tools and plugins will have a unified storage for the test run results.


Requirements
------------
* Python 2.6 or newer installed
* Robot Framework 2.7 or newer installed

Tested and verified on Python 2.7.4 and Robot Framework 2.7.7.

Robot Framework version 2.7.4 or later is recommended as versions prior to 2.7.4
do not support storing total elapsed time for test runs or tags.


How it's used
-------------
The script takes one or more output.xml files as input, initializes the
database schema, and stores the respective results into a database
(robot_results.db by default, can be changed with -b or --database).


Usage
-----
The executable is 'dbbot' in directory 'bin'. Run the script from command-line:

    bin/dbbot [options]

Required options are:

Short format    | Long format             | Description
--------------- |-------------------------| ------------------------------------------
-f              | --files                 | One or more Robot output.xml files

Additional options are:

Short format    | Long format             | Description
--------------- |-------------------------| ------------------------------------------
-k              | --also-keywords         | Parse also suites' and tests' keywords
-v              | --verbose               | Be verbose about the operation
-b DB_FILE_PATH | --database=DB_FILE_PATH | SQLite database for test run results (robot_results.db by default)
-d              | --dry-run               | Do everything except store results into disk

On Windows environments, you might need to rename the executable to have the '.py' file extension
('dbbot' -> 'dbbot.py').


Usage examples
--------------

Typical usage with a single output.xml file:

    dbbot -f atest/testdata/one_suite/output.xml

If the database does not already exist, it's created. Otherwise the test results
are just inserted into the existing database. However, only not existing results are inserted.

The default database is a file named 'robot_results.db'.

Specifying custom database name:

    dbbot -f atest/testdata/one_suite/output.xml -b my_own_database.db

Parsing test run results with keywords included:

    dbbot -k --files atest/testdata/one_suite/output.xml

Giving multiple test run result files at the same time:

    dbbot --files atest/testdata/one_suite/output.xml atest/testdata/one_suite/output_latter.xml


What is stored
--------------
Both the test data (names, content) and test statistics (how many did pass or fail,
possible errors occurred, how long it took to run, etc.) related to suites and test cases
are stored by default. However, keywords are not stored by default as it might take
tens of seconds for massive test runs. Keywords can be stored by using -k or
--also-keywords flag.


Database
--------

You can inspect the created database using the 'sqlite3' command-line tool:

    $ sqlite3 robot_results.db

    sqlite> .tables
    arguments        suite_status     test_run_errors  tests
    keyword_status   suites           test_run_status
    keywords         tag_status       test_runs
    messages         tags             test_status

    sqlite> SELECT count(), tests.id, tests.name
            FROM tests, test_status
            WHERE tests.id == test_status.test_id AND
            test_status.status == "FAIL"
            GROUP BY tests.name;

Please note that when the database is initialized, no indices are created by DbBot.
This is to not slow down the inserts. You might want to add some indices to the
database by hand afterwards to speed up certain queries in your own scripts.

For information about database schema, see 'doc/robot_database.md'.


Directory structure
-------------------

Directory | Description
----------|------------
atests    | Robot Framework powered acceptance tests for DbBot. Also has some test data.
bin       | Contains the executables, mainly 'dbbot'. You may want to append this directory to your PATH.
dbbot     | Contains the packages used by dbbot. You may want to append this directory to your PYTHONPATH if your scripts are inheriting from the abstract classes in the package 'dbbot'
doc       | Mainly technical documentation about the database schema.
examples  | Examples that are using the DbBot created database and extending the 'dbbot' modules.


Use case: Most failing tests
----------------------------
One of the common use cases for DbBot is to get a report of the most commonly failing suites,
tests and keywords. There's an example for this purpose in 'examples/FailBot/bin/failbot'.

Failbot is a Python script used to produce a summary web page of the failing
suites, tests and keywords, using the information stored in the DbBot database.
Please adjust (the barebone) HTML templates in 'examples/FailBot/templates' to your needs.

Another potential use case is to build a script to output the most time-consuming test cases, keywords etc.


Writing your own scripts
------------------------
Please take a look at the modules in 'examples/FailBot/failbot' as an example on how
to extend the DbBot provided classes to your own scripting needs.

You may also want to append the DbBot root directory to your PYTHONPATH
if you are developing something that uses the classes.


Troubleshooting
---------------

Problem: TO BE ASKED

Solution: TO BE ANSWERED
