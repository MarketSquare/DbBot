from sqlite3 import connect


def should_have(count, db_table_name, db_file_path):
    connection = connect(db_file_path)
    cursor = connection.cursor()
    cursor.execute('SELECT count() FROM %s' % db_table_name)
    (number_of_items,) = cursor.fetchone()
    if not number_of_items == int(count):
        raise AssertionError('Expected to have %s but was %s' % (count, number_of_items))
    connection.close()
