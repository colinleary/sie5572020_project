#!/usr/bin/env python3

import warnings
import tkinter as tk
import tkinter.font as tkf
from tkinter import ttk

import pymysql.cursors

__author__ = 'Colin Leary'

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

class EntityFrame(tk.Frame):
    def __init__(self, master, conn, table_name, attr_list):
        super().__init__(master)
        self.master = master
        self.table_name = table_name
        self.attr_list = attr_list
        self.conn = conn

        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=1)

        tree_titles = [title.replace('_', ' ') for title in attr_list]
        self.tree_view = create_tree_view(self, tree_titles)
        self.tree_view.grid(column=0,
                               row=0,
                               columnspan=2,
                               sticky=tk.NSEW)

        delete_button = tk.Button(self, text='Delete', command=self.remove)
        delete_button.grid(row=1, column=0, sticky=tk.NSEW)
        add_button = tk.Button(self, text='Add New', command=self.push_add_window)
        add_button.grid(row=1, column=1, sticky=tk.NSEW)
        self.refresh()

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

        items = [item for item in self.attr_list if not item.lower() == 'id']

        entry_boxes = []

        for i,l in enumerate(items):
            label = tk.Label(win, text=l)
            label.grid(row=i, column=0, columnspan=3, padx=5, pady=5)

            entry = tk.Entry(win)
            entry.grid(row=i, column=3, columnspan=3, padx=5, pady=5)
            entry_boxes.append(entry)

        cancel_button = tk.Button(win, text='Cancel', command=win.destroy)
        cancel_button.grid(row=len(items), column=0, sticky=tk.NSEW, padx=5, pady=5)

        add_action = InsertButtonCallback(self.add, entry_boxes, self.tree_view, win)
        action_button = tk.Button(win, text='Add', command=add_action)
        action_button.grid(row=3, column=3, sticky=tk.NSEW, padx=5, pady=5)


    def add(self, entries, view):
        items = [item for item in self.attr_list if not item.lower() == 'id']

        insert_sql = f'''
            INSERT INTO {self.table_name} ({','.join(items)}) VALUES {tuple(entries)}
        '''

        with self.conn.cursor() as cur:
            cur.execute(insert_sql)

        self.conn.commit()

        self.refresh()

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

        # Create tabs
        self.tabs = ttk.Notebook(self.master)
        self.student_frame = EntityFrame(self.tabs, self.conn, 'students', ['Name'])
        self.tabs.add(self.student_frame, text='Students')

        self.course_frame = EntityFrame(self.tabs, self.conn, 'courses', ['Course_Name', 'Instructor_Name'])
        self.tabs.add(self.course_frame, text='Courses')

        self.assignment_frame = EntityFrame(self.tabs, self.conn, 'assignments', ['Name'])
        self.tabs.add(self.assignment_frame, text='Assignments')

        self.tabs.pack(fill=tk.BOTH, expand=tk.TRUE)

    def __del__(self):
        self.conn.close()

if __name__ == '__main__':
    form = tk.Tk()
    app = App(form)
    form.mainloop()
