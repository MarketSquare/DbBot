import sqlite3


class RobotSqliteDatabase:

    def __init__(self):
        self._connection = None

    def connect_to_database(self, db_file_path):
        self._connection = sqlite3.connect(db_file_path)

    def close_connection(self):
        self._connection.close()

    def row_count_is_equal_to(self, count, db_table_name, db_file_path):
        if not self._number_of_rows_in(db_table_name) == int(count):
            raise AssertionError('Expected to have %s rows but was %s' %
                (count, number_of_items))

    def _number_of_rows_in(self, db_table_name):
        cursor = self._execute('SELECT count() FROM %s' % db_table_name)
        return cursor.fetchone()[0]

    def _execute(self, sql_statement):
        return self._connection.execute(sql_statement)
