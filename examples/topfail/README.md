Topfail
======

Topfail is a Python script used to produce a summary web page about the most failing
suites, tests and keywords, using the information stored in a DbBot database.

Please adjust (the barebone) HTML templates in 'topfail/templates' to your needs.


Requirements
------------
* Python 2.6 or newer installed
* DbBot

Tested and verified on Python 2.7.4.


Usage
-----
The executable is 'topfail' in directory 'bin'. Run the script from command-line:

    ./topfail [options]

Required options are:

Short format    | Long format             | Description
--------------- |-------------------------| ------------------------------------------
-o              | --output                 | Output HTML file name

Additional options are:

Short format    | Long format             | Description
--------------- |-------------------------| ------------------------------------------
-v              | --verbose               | Be verbose about the operation
-b DB_FILE_PATH | --database=DB_FILE_PATH | SQLite database of test run results (robot_results.db by default)

On Windows environments, you might need to rename the executable to have the '.py' file extension
('topfail' -> 'topfail.py').


Usage examples
--------------

The output HTML filename is always required:

    ./topfail -o index.html

If -b/--database is not specified, a database file 'robot_results.db' is used by default.

With a non-default named database:

    ./topfail -f atest/testdata/one_suite/output.xml -b my_own_database.db


Directory structure
-------------------

Directory | Description
----------|------------
bin       | Contains the executable. You may want to append this directory to your PATH.
templates | HTML templates used to produced the summary page.
topfail   | Contains the packages used by topfail. You may want to append this directory to your PYTHONPATH.
