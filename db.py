#!/usr/bin/env python3

import warnings
import pymysql.cursors

__author__ = 'Colin Leary'

class Database:
    def __init__(self, print_func):
        self.conn = None
        self.print_func = print_func

        # Attempt to open the database
        try:
            self.conn = pymysql.connect(host='localhost',
                                        user='python',
                                        db='sie5572020')

        except pymysql.Error as e:
            self.print_func('Cannot open database' + e.args[1])

        # Ensure relevant tables exist
        try:
            self.create_tables()
        except pymysql.Error as e:
            self.print_func('Failed to create tables', e.args[1])

    def __del__(self):
        self.conn.close()

    def remove(self, table, where):
        remove_sql = f'''
            DELETE FROM {table} WHERE {where}
        '''

        success = False

        try:
            with self.conn.cursor() as cur:
                cur.execute(remove_sql)

            self.conn.commit()
            success = True
        except pymysql.Error as e:
            self.print_func('Failed to delete items!' + e.args[1])

        return success

    def insert(self, table, attrs, values, *, ignore_duplicates=False):
        if attrs == '' or values == '':
            return False

        insert_sql = f'''
            INSERT INTO {table} ({attrs}) VALUES {values}
        '''

        success = False

        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_sql)

            self.conn.commit()
            success = True
        except pymysql.Error as e:
            if type(e) is pymysql.IntegrityError and ignore_duplicates:
                success = True

            if not success:
                self.print_func('Failed to add items!' + e.args[1])

        return success

    def get(self, table, attrs, *, where=None):
        select_sql = f'''
            SELECT {attrs} FROM {table}
        '''

        if where is not None:
            select_sql += f'WHERE {where}'

        items = []

        try:
            with self.conn.cursor() as cur:
                cur.execute(select_sql)
                items = cur.fetchall()
        except pymysql.Error as e:
            self.print_func('Failed to get items!' + e.args[1])

        return items

    def create_tables(self):
        create_student_table = '''
            CREATE TABLE IF NOT EXISTS students (
                id INT UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
                name VARCHAR(30) NOT NULL
                )
            '''

        create_assignment_table = '''
            CREATE TABLE IF NOT EXISTS assignments (
                id INT UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
                name VARCHAR(30) NOT NULL
                )
            '''

        create_course_table = '''
            CREATE TABLE IF NOT EXISTS courses (
                id INT UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
                course_name VARCHAR(30) NOT NULL,
                instructor_name VARCHAR(30) NOT NULL
                )
            '''

        create_enrollment_table = '''
            CREATE TABLE IF NOT EXISTS enrollment_data (
                id INT UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
                student_id INT UNSIGNED NOT NULL REFERENCES student(id),
                course_id INT UNSIGNED NOT NULL REFERENCES course(id),
                term VARCHAR(30) NOT NULL,
                CONSTRAINT UNIQUE (student_id, course_id, term)
                )
            '''

        create_enrollment_view = '''
            CREATE OR REPLACE VIEW
                enrollment
            AS SELECT
                e.id,
                e.term,
                e.course_id c_id,
                c.course_name c_name,
                e.student_id s_id,
                s.name s_name
            FROM
                enrollment_data e
            INNER JOIN
                courses c
            ON
                e.course_id = c.id
            INNER JOIN
                students s
            ON
                e.student_id = s.id
            '''

        create_attendance_table = '''
            CREATE TABLE IF NOT EXISTS attendance (
                enrollment_id INT UNSIGNED NOT NULL REFERENCES enrollment(id),
                date DATE NOT NULL,
                CONSTRAINT UNIQUE (enrollment_id, date)
                )
            '''

        create_grade_table = '''
            CREATE TABLE IF NOT EXISTS grades (
                assignment_id INT UNSIGNED NOT NULL REFERENCES assignment(id),
                enrollment_id INT UNSIGNED NOT NULL REFERENCES enrollment(id),
                score INT
            )
        '''

        with self.conn.cursor() as cursor:
            warnings.filterwarnings('ignore')
            cursor.execute(create_student_table)
            cursor.execute(create_assignment_table)
            cursor.execute(create_course_table)
            cursor.execute(create_enrollment_table)
            cursor.execute(create_enrollment_view)
            cursor.execute(create_attendance_table)
            cursor.execute(create_grade_table)
            warnings.filterwarnings('default')

        self.conn.commit()

    def insert_test_data(self):
        pass

if __name__ == '__main__':
    # This module is not callable
    pass
