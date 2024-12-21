import tkinter as tk
import pandas as pd
import pyautogui as gui
from tkinter import simpledialog, messagebox
from ttkthemes import ThemedTk
import ttkbootstrap as ttk
import hashlib
from pygame import *
import cv2
import db as lib
from db import get_users, get_user_by_id, update_user_data, delete_user, add_user, commit_changes, WriteData
from settings import DB_PATH, PHOTO_PATH, CAMERA_INDEX, connect, cursor, EXCEL_LOG_PATH
import time
import os
Gframe = ''

def sendFrame(frame):
    global Gframe
    Gframe = frame

def clear():
    file_path = EXCEL_LOG_PATH  # Specify the path to the Excel file
    # Создаем пустой dataFrame
    df = pd.DataFrame()

    # Сохраняем его в Excel-файл, очищая все данные
    df.to_excel(file_path, index=False)
    print(f"Файл {file_path} был очищен.")


def format_mode():

    password = prompt_password("Администратор", "Введите пароль")
    if password is None:
        WriteData(2, ["Value"], ["03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"], "password")
        return

    entered_password_hash = hashlib.sha256(password.encode()).hexdigest()
    correct_password_hash = "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"

    print(f"Enter password  : {entered_password_hash}")
    print(f"Correct password: {correct_password_hash}")

    if entered_password_hash == correct_password_hash:
        format_ = None
        while format_ not in ("1", "2", "3", "4"):
            format_ = prompt_input("Форматирование", "Что нужно отформатировать?\n"
                                        "1 - БД(всю)\n"
                                        "2 - Пароль от настроек\n"
                                        "3 - Пользователи и посещения\n"
                                        "4 - Прочие данные (кружки, пароли и т.д.)")
        
        sure = messagebox.askyesno("Подтверждение", "Уверены?")
        if sure:
            if format_ == '1':
                cursor.execute("DELETE FROM Users")
                cursor.execute("DELETE FROM Data")
                connect.commit()
                show_message("Администратор", 'Для входа в режим настройки, автоматически установлен пароль "1234"')
                WriteData(2, ["password"], ["03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"], "password")

            elif format_ == '2':
                show_message("Администратор", 'Для входа в режим настройки, автоматически установлен пароль "1234"')
                WriteData(2, ["password"], ["03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"], "password")
                connect.commit()

            elif format_ == '3':
                cursor.execute("DELETE FROM Users")
                connect.commit()

            elif format_ == '4':
                cursor.execute("DELETE FROM Data")
                connect.commit()
                show_message("Администратор", 'Для входа в режим настройки, автоматически установлен пароль "1234"')
                WriteData(2, ["Value"], ["03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"], "password")
    else:
        show_message("Ошибка", "Неверный пароль")



def show_message(title, message):
    messagebox.showinfo(title, message)

def prompt_password(title, prompt):
    return simpledialog.askstring(title, prompt, show='*')

def prompt_input(title, prompt):
    return simpledialog.askstring(title, prompt)

def confirm_action(title, prompt):
    return messagebox.askyesno(title, prompt)

def update_user_list(tree):
    for i in tree.get_children():
        tree.delete(i)
    cursor.execute("SELECT * FROM Users")
    result = cursor.fetchall()
    for row in result:
        tree.insert("", "end", values=row)

def update_data_list(tree):
    for i in tree.get_children():
        tree.delete(i)
    cursor.execute("SELECT * FROM Data")
    result = cursor.fetchall()
    for row in result:
        tree.insert("", "end", values=row)

def search_user(search_var, tree):
    search_term = search_var.get()
    for i in tree.get_children():
        tree.delete(i)
    cursor.execute("SELECT * FROM Users WHERE Name LIKE ?", ('%' + search_term + '%', ))
    result = cursor.fetchall()
    for row in result:
        tree.insert("", "end", values=row)

def clear_search(search_var, tree):
    search_var.set("")
    update_user_list(tree)

def admin_mode():
    
    password = prompt_password("Администратор", "Введите пароль")
    if not password:
        return

    if hashlib.sha256(password.encode()).hexdigest() == "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4":

        root = ThemedTk(theme="Black")  # Используем темную тему
        root.title("Admin Mode")
        root.geometry("800x600")

        tab_control = ttk.Notebook(root)

        users_tab = ttk.Frame(tab_control)
        data_tab = ttk.Frame(tab_control)

        tab_control.add(users_tab, text='Users')
        tab_control.add(data_tab, text='Data')

        tab_control.pack(expand=1, fill='both')

        # Users tab
        users_frame = ttk.Frame(users_tab)
        users_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        search_frame = ttk.Frame(users_tab)
        search_frame.pack(side=tk.TOP, fill=tk.X)

        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=5, pady=5)

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        search_button = ttk.Button(search_frame, text="Search", command=lambda: search_user(search_var, user_tree))
        search_button.pack(side=tk.LEFT, padx=5, pady=5)

        clear_search_button = ttk.Button(search_frame, text="Clear Search", command=lambda: clear_search(search_var, user_tree))
        clear_search_button.pack(side=tk.LEFT, padx=5, pady=5)

        def on_data_double_click(event):
            item = data_tree.selection()[0]
            col = data_tree.identify_column(event.x)
            col_index = int(col.replace("#", "")) - 1
            old_value = data_tree.item(item, "values")[col_index]
            new_value = simpledialog.askstring("Edit Value", "Enter new value:", initialvalue=old_value)

            if new_value:
                col_name = data_tree.heading(col)["text"]
                row_id = data_tree.item(item)["values"][0]  # Assuming the first column is a unique ID
                cursor.execute(f"UPDATE Data SET \"{col_name}\" = ? WHERE ID = ?", (new_value, row_id))
                connect.commit()
                update_data_list(data_tree)

        def on_user_double_click(event):
            item = user_tree.selection()[0]
            col = user_tree.identify_column(event.x)
            col_index = int(col.replace("#", "")) - 1
            old_value = user_tree.item(item, "values")[col_index]
            new_value = simpledialog.askstring("Edit Value", "Enter new value:", initialvalue=old_value)

            if new_value:
                col_name = user_tree.heading(col)["text"]
                user_id = user_tree.item(item)["values"][0]  # Assuming the first column is a unique ID
                cursor.execute(f"UPDATE Users SET \"{col_name}\" = ? WHERE ID = ?", (new_value, user_id))
                connect.commit()
                update_user_list(user_tree)

        user_tree = ttk.Treeview(users_frame, columns=('ID', 'Name', 'PhotoPath'), show='headings')
        user_tree.heading('ID', text='ID')
        user_tree.heading('Name', text='Name')
        user_tree.heading('PhotoPath', text='PhotoPath')

        user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        user_scrollbar = ttk.Scrollbar(users_frame, orient="vertical", command=user_tree.yview)
        user_scrollbar.pack(side=tk.RIGHT, fill='y')

        user_tree.configure(yscroll=user_scrollbar.set)

        update_user_list(user_tree)
        user_tree.bind("<Double-1>", on_user_double_click)

        def add_user():
            global Gframe, ret
            user_name = simpledialog.askstring("Добавление пользователя", "Введите имя пользователя:")
            if not user_name:
                messagebox.showerror("Ошибка", "Имя пользователя не введено.")
                return
            lib.WriteData(1, 'Name', f'"{user_name}"')
            ID = lib.GetData(1, 'ID', f'!Name = "{user_name}"')[0][0]
            print(ID)
            messagebox.showinfo("Фото", "Сейчас будет сделана фотография. Пожалуйста, смотрите в камеру.")
            print('copy frame')
            frame = Gframe.copy()
            
            photo_filename = f"{ID}.jpg"
            photo_path = os.path.join(PHOTO_PATH, photo_filename)
            cv2.imwrite(photo_path, frame)


            try:
                lib.WriteData(1, 'PhotoPath', photo_path, ID)
                messagebox.showinfo("Успех", f"Пользователь {user_name} успешно добавлен.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить пользователя: {e}")
            update_user_list(user_tree)

        def delete_user():
            selected_item = user_tree.selection()[0]
            user_id = user_tree.item(selected_item)['values'][0]
            file_path = lib.GetData(1, 'PhotoPath', user_id)[0][0]
            if os.path.exists(file_path):
                os.remove(file_path)
            cursor.execute(f"DELETE FROM Users WHERE ID = {int(user_id)}")
            connect.commit()
            update_user_list(user_tree)

        def update_user():
            selected_item = user_tree.selection()[0]
            user_id = user_tree.item(selected_item)['values'][0]
            column = prompt_input("Update User", "Enter column to update:")
            value = prompt_input("Update User", "Enter new value:")
            if column and value:
                update_user_data(user_id, value)
                update_user_list(user_tree)

        def commit_changes():
            connect.commit()
            show_message("Admin", "Changes committed!")

        btn_frame = ttk.Frame(users_tab)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        add_btn = ttk.Button(btn_frame, text="Add User", command=add_user)
        add_btn.pack(side=tk.LEFT)

        update_btn = ttk.Button(btn_frame, text="Update User", command=update_user)
        update_btn.pack(side=tk.LEFT)

        delete_btn = ttk.Button(btn_frame, text="Delete User", command=delete_user)
        delete_btn.pack(side=tk.LEFT)

        commit_btn = ttk.Button(btn_frame, text="Commit Changes", command=commit_changes)
        commit_btn.pack(side=tk.LEFT)

        # Data tab
        data_frame = ttk.Frame(data_tab)
        data_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        data_tree = ttk.Treeview(data_frame, columns=('ID', 'Value'), show='headings')
        data_tree.heading('ID', text='ID')
        data_tree.heading('Value', text='Value')

        data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        data_scrollbar = ttk.Scrollbar(data_frame, orient="vertical", command=data_tree.yview)
        data_scrollbar.pack(side=tk.RIGHT, fill='y')

        data_tree.configure(yscroll=data_scrollbar.set)

        update_data_list(data_tree)

        data_tree.bind("<Double-1>", on_data_double_click)

        def add_data():
            key = prompt_input("Add Data", "Enter key:")
            value = prompt_input("Add Data", "Enter value:")
            if key and value:
                cursor.execute(f'INSERT INTO Data (`ID`, `Value`) VALUES (?, ?)', (key, value))
                connect.commit()
                update_data_list(data_tree)

        def update_data():
            selected_item = data_tree.selection()[0]
            name = data_tree.item(selected_item)['values'][0]
            value = prompt_input("Update Data", "Enter new value:")
            if value:
                cursor.execute(f"UPDATE Data SET `Value` = ? WHERE `ID` = ?", (value, name))
                connect.commit()
                update_data_list(data_tree)

        def delete_data():
            selected_item = data_tree.selection()[0]
            name = data_tree.item(selected_item)['values'][0]
            cursor.execute(f"DELETE FROM Data WHERE `ID` = ?", (name,))
            connect.commit()
            update_data_list(data_tree)

        data_btn_frame = ttk.Frame(data_tab)
        data_btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        add_data_btn = ttk.Button(data_btn_frame, text="Add Data", command=add_data)
        add_data_btn.pack(side=tk.LEFT)

        update_data_btn = ttk.Button(data_btn_frame, text="Update Data", command=update_data)
        update_data_btn.pack(side=tk.LEFT)

        delete_data_btn = ttk.Button(data_btn_frame, text="Delete Data", command=delete_data)
        delete_data_btn.pack(side=tk.LEFT)

        root.mainloop()

# admin_mode()