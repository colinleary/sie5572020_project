#!/usr/bin/env python3

import warnings
import tkinter as tk
import tkinter.font as tkf
from tkinter import ttk
from tkinter import messagebox
import tkcalendar as tkc

import pymysql.cursors

__author__ = 'Colin Leary'

# Create a list of the tables & their attributes to be used when the UI interacts with the database
tables = {
    'students': {
        'attrs': ['name'],
        'titles': ['Name']
    },
    'assignments': {
        'attrs': ['name'],
        'titles': ['Name']
    },
    'courses': {
        'attrs': ['course_name', 'instructor_name'],
        'titles': ['Course Name', 'Instructor Name']
    },
}

def create_entity_tables(conn):
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

    with conn.cursor() as cursor:
        warnings.filterwarnings('ignore')
        cursor.execute(create_student_table)
        cursor.execute(create_assignment_table)
        cursor.execute(create_course_table)
        warnings.filterwarnings('default')

    conn.commit()

def create_relationship_tables(conn):
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

    with conn.cursor() as cursor:
        warnings.filterwarnings('ignore')
        cursor.execute(create_enrollment_table)
        cursor.execute(create_enrollment_view)
        cursor.execute(create_attendance_table)
        cursor.execute(create_grade_table)
        warnings.filterwarnings('default')

    conn.commit()

class InsertButtonCallback:
    def __init__(self, func, ebox_list, window):
        self.func = func
        self.ebox_list = ebox_list
        self.window = window

    def __call__(self):
        entries = [ebox.get() for ebox in self.ebox_list]

        if self.func(entries):
            self.window.destroy()

class RemoveButtonCallback:
    def __init__(self, conn, table_name, tree_view, refresh_func):
        self.conn = conn
        self.table_name = table_name
        self.tree_view = tree_view
        self.refresh_func = refresh_func

    def __call__(self):
        remove_sql = f'''
            DELETE FROM {self.table_name} WHERE id=%s
        '''

        with self.conn.cursor() as cur:
            for id in self.tree_view.selection():
                cur.execute(remove_sql, id)

        self.conn.commit()

        self.refresh_func()

class UpdateMenuCallback:
    def __init__(self, set_label, label, set_id, id):
        self.set_label = set_label
        self.label = label
        self.set_id = set_id
        self.id = id

    def __call__(self):
        self.set_label(self.label)
        self.set_id(self.id)

class DbFrame(tk.Frame):
    def __init__(self, master, conn, table_name):
        self.master = master
        self.table_name = table_name
        self.conn = conn
        super().__init__(master)

        self.layout()
        self.refresh()

    def layout(self):
        pass

    def refresh(self):
        pass

class EntityFrame(DbFrame):
    def __init__(self, master, conn, table_name):
        self.attr_list = tables[table_name]['attrs']
        self.titles = tables[table_name]['titles']
        super().__init__(master, conn, table_name)

    def layout(self):
        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=1)

        self.tree_view = ttk.Treeview(self, columns=self.titles, show='headings')

        self.remove = RemoveButtonCallback(self.conn,
                                           self.table_name,
                                           self.tree_view,
                                           self.refresh)

        for col in self.titles:
            self.tree_view.heading(col, text=col)

        self.tree_view.grid(column=0,
                               row=0,
                               columnspan=2,
                               sticky=tk.NSEW)

        delete_button = tk.Button(self, text='Delete', command=self.remove)
        delete_button.grid(row=1, column=0, sticky=tk.NSEW)
        add_button = tk.Button(self, text='Add New', command=self.push_add_window)
        add_button.grid(row=1, column=1, sticky=tk.NSEW)

    def refresh(self):
        get_all = f'''
            SELECT {'id,'+','.join(self.attr_list)} FROM {self.table_name}
        '''

        # Clear out the tree so we can add everything back in
        self.tree_view.delete(*self.tree_view.get_children())

        with self.conn.cursor() as cur:
            cur.execute(get_all)
            res = cur.fetchall()
            for item in res:
                self.tree_view.insert('', 'end', item[0], values=item[1:])

    def push_add_window(self):
        win = tk.Toplevel()
        x = self.master.master.winfo_x()
        y = self.master.master.winfo_y()
        win.geometry(f'+{x}+{y}')
        win.title('Add New')

        tk.Grid.columnconfigure(win, 1, weight=1)
        tk.Grid.columnconfigure(win, 2, weight=1)

        entry_boxes = []
        h = 0

        for i,l in enumerate(self.titles):
            label = tk.Label(win, text=l+':')
            label.grid(row=i, column=0, padx=5, pady=5)

            entry = tk.Entry(win, )
            entry.grid(row=i, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
            entry_boxes.append(entry)
            h = entry.winfo_reqheight()

        cancel_button = tk.Button(win, text='Cancel', command=win.destroy)
        cancel_button.grid(row=len(self.titles), column=1, sticky=tk.EW, padx=5, pady=(h, 0))

        add_action = InsertButtonCallback(self.add, entry_boxes, win)
        action_button = tk.Button(win, text='Add', command=add_action)
        action_button.grid(row=len(self.titles), column=2, sticky=tk.EW, padx=5, pady=(h, 0))


    def add(self, entries):
        a = ','.join(s for s in self.attr_list)
        e = ','.join(f'"{s}"' for s in entries)

        insert_sql = f'''
            INSERT INTO {self.table_name} ({a}) VALUES ({e})
        '''

        with self.conn.cursor() as cur:
            cur.execute(insert_sql)

        self.conn.commit()

        self.refresh()

        return True

class EnrollmentFrame(DbFrame):
    def __init__(self, master, conn):
        self.INVALID_TERM_STR = 'Select Term'
        self.INVALID_COURSE_STR = 'Select Course'
        self.INVALID_ID = -1
        self.term_str = tk.StringVar(value=self.INVALID_TERM_STR)
        self.course_id = tk.IntVar(value = self.INVALID_ID)
        self.course_str = tk.StringVar(value=self.INVALID_COURSE_STR)
        super().__init__(master, conn, 'enrollment')

    def layout(self):
        tk.Grid.rowconfigure(self, 1, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=1)

        # Create drop-down to select term
        self.term_str.trace('w', self.update_course_menu)
        self.term_menu = tk.OptionMenu(self, self.term_str, None)
        self.term_menu.grid(column=0, row=0)

        # Create drop-down to select course
        self.course_id.trace_add('write', self.update_student_list)
        # self.course_str.trace('w', self.update_student_list)
        self.course_menu = tk.OptionMenu(self, self.course_str, None)
        self.course_menu.grid(column=1, row=0)

        # Create tree view to show students enrolled
        self.tree_view = ttk.Treeview(self, columns='items', show='headings')
        self.tree_view.heading(0, text='Students')
        self.tree_view.grid(column=0,
                               row=1,
                               columnspan=2,
                               sticky=tk.NSEW)

        self.remove = RemoveButtonCallback(self.conn,
                                           'enrollment_data',
                                           self.tree_view,
                                           self.refresh)

        delete_button = tk.Button(self, text='Delete', command=self.remove)
        delete_button.grid(row=2, column=0, sticky=tk.NSEW)
        add_button = tk.Button(self, text='Add New', command=self.push_add_window)
        add_button.grid(row=2, column=1, sticky=tk.NSEW)

    def push_add_window(self):
        win = tk.Toplevel()
        x = self.master.master.winfo_x()
        y = self.master.master.winfo_y()
        win.geometry(f'+{x}+{y}')
        win.title('Add New')

        tk.Grid.columnconfigure(win, 1, weight=1)
        tk.Grid.columnconfigure(win, 2, weight=1)

        label = tk.Label(win, text='Term:')
        label.grid(row=0, column=0, padx=5, pady=5)

        entry = tk.Entry(win)
        entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        if self.term_str.get() != self.INVALID_TERM_STR:
            entry.insert(0, self.term_str.get())

        # entry_boxes = []
        h = entry.winfo_reqheight()

        label = tk.Label(win, text='Course:')
        label.grid(row=1, column=0, padx=5, pady=5)

        # Create drop-down to select course
        course_var = tk.StringVar(value=self.course_str.get())
        course_id = tk.IntVar(value=self.course_id.get())

        course_menu = self.build_option_menu(self.conn, ['id', 'course_name'], 'courses', win, course_var, course_id)
        course_menu.grid(column=1, row=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)

        label = tk.Label(win, text='Student:')
        label.grid(row=2, column=0, padx=5, pady=5)

        # Create drop-down to select student
        student_var = tk.StringVar(value='Select Student')
        student_id = tk.IntVar(value=self.INVALID_ID)

        student_menu = self.build_option_menu(self.conn, ['id', 'name'], 'students', win, student_var, student_id)
        student_menu.grid(column=1, row=2, columnspan=2, padx=5, pady=5, sticky=tk.EW)

        cancel_button = tk.Button(win, text='Cancel', command=win.destroy)
        cancel_button.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=(h, 0))

        data = [entry, course_id, student_id]

        add_action = InsertButtonCallback(self.add, data, win)
        action_button = tk.Button(win, text='Add', command=add_action)
        action_button.grid(row=3, column=2, sticky=tk.EW, padx=5, pady=(h, 0))

    def build_option_menu(self, conn, attrs, table, win, str_var, id_var):
        with conn.cursor() as cur:
            get_data = f'''
                SELECT {','.join(a for a in attrs)} FROM {table}
                '''

            cur.execute(get_data)

        data = cur.fetchall()
        option_menu = tk.OptionMenu(win, str_var, [])

        menu = option_menu['menu']
        menu.delete(0, 'end')

        for item in data:
            label = f'{item[1]}'
            id = item[0]
            menu.add_command(label=label,
                             command=UpdateMenuCallback(str_var.set,
                                                        label,
                                                        id_var.set,
                                                        id))

        return option_menu

    def add(self, data):
        if data[0] == '' or data[1] == self.INVALID_ID or data[2] == self.INVALID_ID:
            return False

        success = True
        with self.conn.cursor() as cur:
            insert_sql = f'''INSERT INTO enrollment_data (term, course_id, student_id) VALUES
                ('{data[0]}',{data[1]},{data[2]})
            '''
            try:
                cur.execute(insert_sql)
            except pymysql.IntegrityError as e:
                messagebox.showinfo("Error", "Cannot insert! Likely due to duplicate")
                success = False

        self.conn.commit()

        self.refresh()

        return success

    def update_term_menu(self):
        with self.conn.cursor() as cur:
            get_terms = '''SELECT DISTINCT(term) from enrollment'''
            cur.execute(get_terms)

            term_list = [term[0] for term in cur.fetchall()]

        # Clear out existing menu items & fill with list
        menu = self.term_menu['menu']
        menu.delete(0, 'end')
        for term in term_list:
            menu.add_command(label=term,
                             command=lambda value=term: self.term_str.set(value))

        if self.term_str.get() not in term_list:
            self.term_str.set(self.INVALID_TERM_STR)

    def update_course_menu(self, *args):
        if self.term_str.get() == self.INVALID_TERM_STR:
            self.course_id.set(self.INVALID_ID)
            self.course_str.set(self.INVALID_COURSE_STR)
            return

        # Get course list for a given term
        with self.conn.cursor() as cur:
            get_courses = f'''SELECT DISTINCT c_name, c_id FROM enrollment
                                WHERE term="{self.term_str.get()}"'''

            cur.execute(get_courses)

            course_data = cur.fetchall()

        # Replace menu
        menu = self.course_menu['menu']
        menu.delete(0, 'end')
        for course in course_data:
            l = f'{course[0]}'
            i = course[1]
            menu.add_command(label=l,
                             command=UpdateMenuCallback(self.course_str.set, l,
                                                        self.course_id.set, i))

        if self.course_id.get() not in [course[1] for course in course_data]:
            self.course_id.set(self.INVALID_ID)
            self.course_str.set(self.INVALID_COURSE_STR)

    def update_student_list(self, *args):
        # Clear everything out of tree
        self.tree_view.delete(*self.tree_view.get_children())

        if self.course_str.get() == self.INVALID_COURSE_STR:
            return

        # Get list of students
        with self.conn.cursor() as cur:
            get_students = f'''SELECT id,s_name FROM enrollment
                                WHERE term="{self.term_str.get()}"
                                AND c_id={self.course_id.get()}'''

            cur.execute(get_students)

            for student in cur.fetchall():
                self.tree_view.insert('', 'end', student[0], values=f'"{student[1]}"')

    def refresh(self):
        self.update_term_menu()
        self.update_course_menu()
        self.update_student_list()

# The attendance frame is almost identical to the enrollment frame
class AttendanceFrame(EnrollmentFrame):
    def __init__(self, master, conn):
        super().__init__(master, conn)

    def layout(self):
        tk.Grid.rowconfigure(self, 1, weight=1)
        for c in range(6):
            tk.Grid.columnconfigure(self, c, weight=1)

        # Create drop-down to select term
        self.term_str.trace('w', self.update_course_menu)
        self.term_menu = tk.OptionMenu(self, self.term_str, None)
        self.term_menu.grid(column=0, row=0, columnspan=2)

        # Create drop-down to select course
        self.course_id.trace_add('write', self.update_student_list)
        # self.course_str.trace('w', self.update_student_list)
        self.course_menu = tk.OptionMenu(self, self.course_str, None)
        self.course_menu.grid(column=2, row=0, columnspan=2)

        # Create date-picker
        self.date_picker = tkc.DateEntry(self)
        self.date_picker.grid(column=5, row=0)
        self.date = self.date_picker.get_date()
        self.date_picker.bind('<<DateEntrySelected>>', self.update_date)

        # Create tree view to show students enrolled
        self.tree_view = ttk.Treeview(self, columns=['students', 'present'], show='headings')
        self.tree_view.heading(0, text='Students')
        self.tree_view.heading(1, text='Present')
        self.tree_view.grid(column=0,
                               row=1,
                               columnspan=6,
                               sticky=tk.NSEW)

        not_present_button = tk.Button(self, text='Not Present', command=self.mark_not_present)
        not_present_button.grid(row=2, column=0, columnspan=3, sticky=tk.NSEW)
        present_button = tk.Button(self, text='Present', command=self.mark_present)
        present_button.grid(row=2, column=3, columnspan=3, sticky=tk.NSEW)

    def mark_not_present(self):
        remove_attendance_sql = f'''DELETE FROM attendance
            WHERE enrollment_id = %s
            AND date = "{self.date}"'''

        with self.conn.cursor() as cur:
            for s in self.tree_view.selection():
                cur.execute(remove_attendance_sql, s)

        self.conn.commit()

        self.refresh()

    def mark_present(self):
        add_attendance_sql = f'''INSERT INTO attendance
            (enrollment_id, date) VALUES
            (%s, "{self.date}")
        '''

        with self.conn.cursor() as cur:
            for s in self.tree_view.selection():
                try:
                    cur.execute(add_attendance_sql, s)
                except pymysql.IntegrityError:
                    pass

        self.conn.commit()

        self.refresh()

    def update_date(self, *args):
        self.date = self.date_picker.get_date()
        self.refresh()

    def update_student_list(self, *args):
        # Clear everything out of tree
        self.tree_view.delete(*self.tree_view.get_children())

        if self.course_str.get() == self.INVALID_COURSE_STR:
            return

        # Get attendance
        with self.conn.cursor() as cur:
            get_attendance = f'''SELECT enrollment_id FROM attendance
                                WHERE date="{self.date}"'''

            cur.execute(get_attendance)

            present = [i[0] for i in cur.fetchall()]

        # Get list of students
        with self.conn.cursor() as cur:

            get_students = f'''SELECT id,s_name FROM enrollment
                                WHERE term="{self.term_str.get()}"
                                AND c_id={self.course_id.get()}'''

            cur.execute(get_students)

            for student in cur.fetchall():
                v = [f'{student[1]}']
                if student[0] in present:
                    v.append('X')

                self.tree_view.insert('', 'end', student[0], values=v)

class App:
    def __init__(self, master):
        # Create connection
        self.master = master

        self.conn = pymysql.connect(host='localhost',
                                    user='python',
                                    db='sie5572020')

        master.title('SIE557 Project')

        # Get screen size
        sw = master.winfo_screenwidth()
        sh = master.winfo_screenheight()

        # Determine window size
        w = int(sw * .6)
        h = int(sh * .6)

        # Center window in screen
        x = int(sw / 2 - w / 2)
        y = int(sh / 2 - h / 2)

        master.geometry(f'{w}x{h}+{x}+{y}')

        # Make sure tables exists
        create_entity_tables(self.conn)
        create_relationship_tables(self.conn)

        fname = ttk.Style().lookup('TreeView', 'font')
        fontheight = tkf.Font(name=fname, exists=tk.TRUE).metrics('linespace')

        style = ttk.Style()
        style.configure('Treeview', rowheight=int(fontheight))

        self.tabs = ttk.Notebook(self.master)

        self.attentance_frame = AttendanceFrame(self.tabs, self.conn)
        self.tabs.add(self.attentance_frame, text='Attendance')

        # Create Entity tabs
        self.student_frame = EntityFrame(self.tabs, self.conn, 'students')
        self.tabs.add(self.student_frame, text='Students')

        self.course_frame = EntityFrame(self.tabs, self.conn, 'courses')
        self.tabs.add(self.course_frame, text='Courses')

        self.assignment_frame = EntityFrame(self.tabs, self.conn, 'assignments')
        self.tabs.add(self.assignment_frame, text='Assignments')

        # Create Relationship tabs
        self.enrollment_frame = EnrollmentFrame(self.tabs, self.conn)
        self.tabs.add(self.enrollment_frame, text='Enrollment')



        self.tabs.pack(fill=tk.BOTH, expand=tk.TRUE)

    def __del__(self):
        self.conn.close()

if __name__ == '__main__':
    form = tk.Tk()
    app = App(form)
    form.mainloop()
