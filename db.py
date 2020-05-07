#!/usr/bin/env python3

import warnings
import pymysql.cursors
import random

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
                name VARCHAR(30) NOT NULL,
                CONSTRAINT UNIQUE (name)
                )
            '''

        create_assignment_table = '''
            CREATE TABLE IF NOT EXISTS assignments (
                id INT UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
                name VARCHAR(30) NOT NULL,
                CONSTRAINT UNIQUE (name)
                )
            '''

        create_course_table = '''
            CREATE TABLE IF NOT EXISTS courses (
                id INT UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
                course_name VARCHAR(30) NOT NULL,
                instructor_name VARCHAR(30) NOT NULL,
                CONSTRAINT UNIQUE (course_name,instructor_name)
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
        students = [
            ('Fariha Quinn'),
            ('Giovanni Hagan'),
            ('Lyla-Rose Wyatt'),
            ('Nolan Knights'),
            ('Aarush Mullen'),
            ('Akeel Mccarty'),
            ('Riaan Mason'),
            ('Cain Nichols'),
            ('Caitlyn Horn'),
            ('Luc Park')
        ]

        insert_students = f'''
            INSERT INTO students (name) VALUES {','.join(f'("{s}")' for s in students)}
        '''

        courses = [
            ('Acacia Bob', 'Alien Bioengineering'),
            ('Shyla Molloy', 'Planetary Biology'),
            ('Lorena Archer', 'Life Gardening'),
            ('Carys Joyce', 'Foreign Drama'),
            ('Gurveer Hicks', 'Alien Mathematics'),
            ('Susie Adams', 'Alien Ethics'),
            ('Henry Mcnamara', 'Extinct Language Literature'),
            ('Henrietta Person', 'Alien Biology'),
            ('Krista Miranda', 'Alien Tactics and Strategy'),
            ('Tasnia Avery', 'Ward Casting')
        ]

        insert_courses = f'''
            INSERT INTO courses
                (instructor_name, course_name)
            VALUES
                {','.join(f'{s}' for s in courses)}
        '''

        insert_assignments = f'''
            INSERT INTO assignments
                (name)
            VALUES
                {','.join(f'("Homework {i+1}")' for i in range(10))}
        '''

        with self.conn.cursor() as cur:
            try:
                cur.execute(insert_students)
            except:
                pass

            try:
                cur.execute(insert_courses)
            except:
                pass

            try:
                cur.execute(insert_assignments)
            except:
                pass

        self.conn.commit()

        student_ids = []
        course_ids = []
        with self.conn.cursor() as cur:
            try:
                cur.execute('SELECT id FROM students')
                student_ids = [id[0] for id in cur.fetchall()]
            except:
                pass

            try:
                cur.execute('SELECT id FROM courses')
                course_ids = [id[0] for id in cur.fetchall()]
            except:
                pass

        terms = [
            ('Spring 2020'),
            ('Fall 2019'),
            ('Spring 2019'),
            ('Fall 2018'),
            ('Spring 2018'),
            ('Fall 2017')
        ]

        values = []
        for term in terms:
            n = random.randint(0, len(course_ids))
            c_ids = random.sample(course_ids, n)
            for c_id in c_ids:
                m = random.randint(0, len(student_ids))
                s_ids = random.sample(student_ids, m)
                for s_id in s_ids:
                    values.append((term,c_id,s_id))

        with self.conn.cursor() as cur:
            insert_enrollment = '''
                INSERT INTO enrollment_data
                    (term, course_id, student_id)
                VALUES
                    (%s, %s, %s)
            '''

            try:
                cur.executemany(insert_enrollment, values)
            except:
                pass

        self.conn.commit()

if __name__ == '__main__':
    # This module is not callable
    pass
