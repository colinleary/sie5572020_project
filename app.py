#!/usr/bin/env python3

import warnings
import tkinter as tk
import tkinter.font as tkf
from tkinter import ttk

import pymysql.cursors

__author__ = 'Colin Leary'

# Create a list of the tables & their attributes to be used when the UI interacts with the database
tables = {
    'students' : {
        'attrs': ['name'],
        'titles': ['Name']
    },
    'assignments' : {
        'attrs': ['name'],
        'titles': ['Name']
    },
    'courses' : {
        'attrs': ['course_name', 'instructor_name'],
        'titles': ['Course Name', 'Instructor Name']
    },
    'enrollment': {
        'attrs': ['student_id', 'course_id', 'term'],
        'titles': ['Student', 'Course', 'Term']
    },
    'attendance': {
        'attrs': ['enrollment_id', 'date'],
        'titles': ['Enrollment', 'Date']
    },
    'grades': {
        'attrs': ['assignment_id', 'enrollment_id', 'score'],
        'titles': ['Assignment', 'Enrollment', 'Score']
    }
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
        CREATE TABLE IF NOT EXISTS enrollment (
            id INT UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
            student_id INT UNSIGNED NOT NULL REFERENCES student(id),
            course_id INT UNSIGNED NOT NULL REFERENCES course(id),
            term VARCHAR(30)
            )
        '''

    create_attendance_table = '''
        CREATE TABLE IF NOT EXISTS attendance (
            enrollment_id INT UNSIGNED NOT NULL REFERENCES enrollment(id),
            date DATE NOT NULL
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
        cursor.execute(create_attendance_table)
        cursor.execute(create_grade_table)
        warnings.filterwarnings('default')

    conn.commit()

def create_tree_view(frame, cols):
    view = ttk.Treeview(frame, columns=cols, show='headings')
    for col in cols:
        view.heading(col, text=col)

    fname = ttk.Style().lookup('TreeView', 'font')
    fontheight = tkf.Font(name=fname, exists=tk.TRUE).metrics('linespace')

    style = ttk.Style()
    style.configure('Treeview', rowheight=int(fontheight))

    return view

class InsertButtonCallback:
    def __init__(self, func, ebox_list, view, window):
        self.func = func
        self.ebox_list = ebox_list
        self.view = view
        self.window = window

    def __call__(self):
        entries = [ebox.get() for ebox in self.ebox_list]

        self.func(entries, self.view)
        self.window.destroy()

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

        for col in self.titles:
            self.tree_view.heading(col, text=col)

        fname = ttk.Style().lookup('TreeView', 'font')
        fontheight = tkf.Font(name=fname, exists=tk.TRUE).metrics('linespace')

        style = ttk.Style()
        style.configure('Treeview', rowheight=int(fontheight))

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

    def remove(self):
        remove_sql = f'''
            DELETE FROM {self.table_name} WHERE id=%s
        '''

        with self.conn.cursor() as cur:
            for id in self.tree_view.selection():
                print(f'Removing ID:{id}')
                cur.execute(remove_sql, id)

        self.conn.commit()

        self.refresh()

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

        add_action = InsertButtonCallback(self.add, entry_boxes, self.tree_view, win)
        action_button = tk.Button(win, text='Add', command=add_action)
        action_button.grid(row=len(self.titles), column=2, sticky=tk.EW, padx=5, pady=(h, 0))


    def add(self, entries, view):
        a = ','.join(s for s in self.attr_list)
        e = ','.join(f'"{s}"' for s in entries)

        insert_sql = f'''
            INSERT INTO {self.table_name} ({a}) VALUES ({e})
        '''

        with self.conn.cursor() as cur:
            cur.execute(insert_sql)

        self.conn.commit()

        self.refresh()

class RelationshipFrame(EntityFrame):
    def __init__(self, master, conn, table_name):
        super().__init__(master, conn, table_name)

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

        self.tabs = ttk.Notebook(self.master)

        # Create Entity tabs
        self.student_frame = EntityFrame(self.tabs, self.conn, 'students')
        self.tabs.add(self.student_frame, text='Students')

        self.course_frame = EntityFrame(self.tabs, self.conn, 'courses')
        self.tabs.add(self.course_frame, text='Courses')

        self.assignment_frame = EntityFrame(self.tabs, self.conn, 'assignments')
        self.tabs.add(self.assignment_frame, text='Assignments')

        # Create Relationship tabs
        self.enrollment_frame = RelationshipFrame(self.tabs, self.conn, 'enrollment')
        self.tabs.add(self.enrollment_frame, text='Enrollment')

        self.tabs.pack(fill=tk.BOTH, expand=tk.TRUE)

    def __del__(self):
        self.conn.close()

if __name__ == '__main__':
    form = tk.Tk()
    app = App(form)
    form.mainloop()
