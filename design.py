import sys
import copy
from db import GetRaw, execute
from PyQt6.QtWidgets import QApplication, QWidget, QTableWidgetItem, QPushButton, QMessageBox, QLabel, QVBoxLayout
from PyQt6.QtWidgets import QInputDialog, QDialog
from PyQt6.uic import loadUi
import settings as s
from settings import CAMERA_INDEX
import cv2
import threading
import time

print('Start')

data = GetRaw('''SELECT Value FROM Data WHERE `ID` LIKE "s%"''')

SICELS = [str(x[0]).split("|")[0] for x in data]
PATH_TO_PHOTO_DERICTORY = s.PHOTO_PATH
camReady = False
frame = None
exit_ = False

class SicelsWindow(QDialog):
    def __init__(self):
        super().__init__()
        loadUi('C:\prog\SASA\Sicels.ui', self)
        self.sicels = []
        self.ready = False
        # Привязка сигналов к слотам
        self.OK_button.clicked.connect(self.on_ok_button_clicked)

    def setSicels(self, sicels_list):
        # Удаляем все существующие QPushButton, кроме первого
        layout = self.verticalLayout_2
        while layout.count() > 1:
            item = layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        # Добавляем новые QPushButton на основе списка имен кружков
        for sicel in sicels_list:
            button = QPushButton(sicel)
            button.setCheckable(True)  # Делаем кнопку переключаемой
            button.setStyleSheet("background-color: white;")  # Начальный цвет
            button.toggled.connect(lambda checked, b=button: self.on_button_toggled(checked, b))
            layout.addWidget(button)

    def on_button_toggled(self, checked, button):
        if checked:
            button.setStyleSheet("background-color: green;")  # Цвет при нажатии
        else:
            button.setStyleSheet("background-color: white;")  # Цвет при отпускании

    def on_ok_button_clicked(self):
        self.sicels = []
        layout = self.verticalLayout_2
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QPushButton):
                if item.widget().isChecked():
                    self.sicels.append(item.widget().text())
        self.close()
        self.ready = True

    def getSicels(self):
        return self.sicels

    def setButtons(self, button_names):
        layout = self.verticalLayout_2
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QPushButton):
                button = item.widget()
                if button.text() in button_names:
                    button.setChecked(True)
                    button.setStyleSheet("background-color: green;")  # Цвет при нажатии
                else:
                    button.setChecked(False)
                    button.setStyleSheet("background-color: white;")  # Цвет при отпускании

class CustomMessageBox(QDialog):
    def __init__(self, message, title):
        super().__init__()
        self.setWindowTitle(title)

        layout = QVBoxLayout()

        self.label = QLabel(message)
        layout.addWidget(self.label)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

def camera_loader():
    global frame, camReady, exit_
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    while exit_ == False:
        ret, frame = camera.read()
        if ret:
            cv2.imshow('CamAdmin', frame)
            cv2.waitKey(1)
            if not camReady:
                camReady = True
                print("Камера готова к работе")

    camera.release()
    cv2.destroyAllWindows()

def alert(text, title='Информация'):
    msg_box = CustomMessageBox(text, title)
    msg_box.exec()

def sicels(klasses, set=[]) -> list:
    dialog = SicelsWindow()
    dialog.setSicels(klasses)
    dialog.setButtons(set)
    dialog.exec()
    print(dialog.getSicels())
    return dialog.getSicels()


class MyApp(QWidget):
    global Gframe
    def clearSearchFunc(self):
        self.SearchSps = {'ID': [], 
                          'Name': [], 
                          'Sicels': [], 
                          'PhotoPath': [], 
                          'PrevTime' : [],
                          'PrevDay' : [],
                          'FaceEncoding' : []}

    def __init__(self):
        super().__init__()
        loadUi('C:\prog\SASA\design.ui', self)

        # Привязка сигналов к слотам
        self.search_butt.clicked.connect(self.on_search_clicked)
        self.addUser.clicked.connect(self.on_add_user_clicked)
        self.deleteUser.clicked.connect(self.on_delete_user_clicked)
        self.addData.clicked.connect(self.on_add_data_clicked)
        self.deleteData.clicked.connect(self.on_delete_data_clicked)
        self.clearSearch.clicked.connect(self.on_clear_search_clicked)

        self.saveUsers.clicked.connect(self.save_users_data)
        self.resetUsers.clicked.connect(self.reset_users)
        self.saveData.clicked.connect(self.save_data_data)
        self.resetData.clicked.connect(self.reset_data)
        self.searchParam.currentIndexChanged.connect(self.on_combobox_changed)

        data = GetRaw('''SELECT * FROM Users''')
        # print(*data, sep='\n')

        self.dataUsers = {'ID': [str(x[0]) for x in data], 
                          'Name': [str(x[1]) for x in data], 
                          'Sicels': [str(x[5]) for x in data], 
                          'PhotoPath': [str(x[2]) for x in data], 
                          'PrevTime' : [str(x[3]) for x in data],
                          'PrevDay' : [str(x[4]) for x in data],
                          'FaceEncoding' : [str(x[6]) for x in data]}
        
        data = GetRaw('''SELECT * FROM Data''')

        self.dataData = {'ID': [str(x[0]) for x in data], 'Value': [str(x[1]) for x in data]}

        self.buffDataUsers = copy.deepcopy(self.dataUsers)
        self.buffDataData = copy.deepcopy(self.dataData)
        
        self.Search = False
        self.SearhKey = self.searchParam.currentText()
        self.clearSearchFunc()
        self.searchParam.addItems(self.buffDataUsers.keys())
        self.searchParam.setCurrentIndex(1)

        # Инициализация таблиц
        self.init_users_table()
        self.init_data_table()

        self.table_Users.cellDoubleClicked.connect(self.tableDoubleClicked)
    
    def tableDoubleClicked(self, row, column):
        if column == 2:
            print('Now', str(self.buffDataUsers['Sicels'][row]).split('/'))
            s = sicels(SICELS, str(self.buffDataUsers['Sicels'][row]).split('/'))
            if s != []:
                self.buffDataUsers['Sicels'][row] = '/'.join(s)

                self.init_users_table()

                self.table_Users.clearSelection()


    def on_combobox_changed(self):
        self.SearhKey = self.searchParam.currentText()

    def init_users_table(self):
        # Получаем ключи словаря
        keys = list(self.buffDataUsers.keys())

        self.table_Users.setRowCount(len(self.SearchSps[keys[0]] if self.Search else self.buffDataUsers[keys[0]]))
        self.table_Users.setColumnCount(len(keys))
        self.table_Users.setHorizontalHeaderLabels(keys)

        # Заполняем модель данными
        if self.Search:
            for keyIndex in range(len(keys)):
                key = keys[keyIndex]
                for index in range(len(self.SearchSps[key])):
                    item = QTableWidgetItem(str(self.SearchSps[key][index]))
                    self.table_Users.setItem(index, keyIndex, item)
        else:
            for keyIndex in range(len(keys)):
                key = keys[keyIndex]
                for index in range(len(self.buffDataUsers[key])):
                    item = QTableWidgetItem(str(self.buffDataUsers[key][index]))
                    self.table_Users.setItem(index, keyIndex, item)

    def init_data_table(self):
        # Получаем ключи словаря
        keys = list(self.buffDataData.keys())

        # Устанавливаем количество строк и столбцов в QTableWidget
        self.table_Data.setRowCount(len(self.buffDataData[keys[0]]))
        self.table_Data.setColumnCount(len(keys))
        self.table_Data.setHorizontalHeaderLabels(keys)

        # Заполняем QTableWidget данными
        
        for keyIndex in range(len(keys)):
            key = keys[keyIndex]
            for index in range(len(self.buffDataData[key])):
                item = QTableWidgetItem(str(self.buffDataData[key][index]))
                self.table_Data.setItem(index, keyIndex, item)

    def get_selected_rows(self, table):
        selected_indexes = table.selectedIndexes()
        if not selected_indexes:
            return []
        selected_rows = set(index.row() for index in selected_indexes)
        return list(selected_rows)
    

    def on_clear_search_clicked(self):
        self.Search = False
        self.clearSearchFunc()
        self.ToSearch.setText('')
        self.init_users_table()

    def on_search_clicked(self):
        search_text = self.ToSearch.text()
        self.Search = True
        key = self.SearhKey
        self.clearSearchFunc()
        print(f"Searching for: {search_text} in {key}")
        for index in range(len(self.buffDataUsers[key])):
            if search_text in self.buffDataUsers[key][index]:
                keys = self.SearchSps.keys()
                for key2 in keys:
                    self.SearchSps[key2].append(self.buffDataUsers[key2][index])
        print('ITG:', self.SearchSps)

        self.init_users_table()

    def on_add_user_clicked(self):
        print("Add User button clicked")
        keys = self.buffDataUsers.keys()

        for key in keys:
            if key not in ['ID', 'PhotoPath']:
                self.buffDataUsers[key].append('')
            else:
                if key in ['ID']:
                    if len(self.buffDataUsers[key]) != 0:
                        LastID = int(self.buffDataUsers[key][-1])
                        self.buffDataUsers[key].append(str(LastID+1))
                    else:
                        self.buffDataUsers[key].append('0')
                elif key in ['PhotoPath']:
                    print('Photo')
                    if len(self.buffDataUsers['ID']) != 0:
                        ID = int(self.buffDataUsers['ID'][-1])
                    else:
                        ID = 0
                    PHOTO_PATH = f'{PATH_TO_PHOTO_DERICTORY}{ID}.jpg'
                    self.buffDataUsers[key].append(PHOTO_PATH)
                    alert("Сейчас будет сделана фотография. Пожалуйста, смотрите в камеру.", "Фото")
                    from main import frame
                    cv2.imwrite(PHOTO_PATH, frame)

        self.init_users_table()

    def on_delete_user_clicked(self):
        print("Delete User button clicked")
        toDelete = self.get_selected_rows(self.table_Users)
        print('to delete', toDelete)
        keys = list(self.buffDataUsers.keys())
        for key in keys:
            for index in sorted(toDelete, reverse=True):
                self.buffDataUsers[key].pop(index)
        # Добавьте логику для удаления пользователя
        self.init_users_table()

    def on_add_data_clicked(self):
        print("Add Data button clicked")
        keys = self.buffDataData.keys()

        for key in keys:
            self.buffDataData[key].append(' ')

        self.init_data_table()
        

    def on_delete_data_clicked(self):
        print("Delete Data button clicked")
        toDelete = self.get_selected_rows(self.table_Data)
        print('to delete', toDelete)
        keys = list(self.buffDataData.keys())
        for key in keys:
            for index in sorted(toDelete, reverse=True):
                self.buffDataData[key].pop(index)
        self.init_data_table()

    def reset_users(self):
        print('reset users')
        print(self.dataUsers)
        self.buffDataUsers = copy.deepcopy(self.dataUsers)
        self.init_users_table()

    def save_users_data(self):
        returnSearch = self.Search
        if self.Search:
            self.Search = False
            self.init_users_table()

        keys = list(self.buffDataUsers.keys())

        for keyIndex in range(len(keys)):
            key = keys[keyIndex]
            self.dataUsers[key] = [self.table_Users.item(row, keyIndex).text() for row in range(self.table_Users.rowCount())]

        self.buffDataUsers = copy.deepcopy(self.dataUsers)

        execute('''DELETE FROM Users WHERE 1 = 1''')

        keys = list(self.buffDataUsers.keys())

        for Index in range(len(self.buffDataUsers['ID'])):
            print(f'''INSERT INTO Users ({", ".join(keys)}) VALUES ({self.buffDataUsers[keys[0]][Index]}, 
                    "{self.buffDataUsers[keys[1]][Index]}",
                    "{self.buffDataUsers[keys[2]][Index]}",
                    "{self.buffDataUsers[keys[3]][Index]}",
                    {self.buffDataUsers[keys[4]][Index] if self.buffDataUsers[keys[4]][Index] != '' else '0'},
                    {self.buffDataUsers[keys[5]][Index] if self.buffDataUsers[keys[5]][Index] != '' else '0'},
                    Ecodings")''')
            execute(f'''INSERT INTO Users ({", ".join(keys)}) VALUES ({self.buffDataUsers[keys[0]][Index]}, 
                    "{self.buffDataUsers[keys[1]][Index]}",
                    "{self.buffDataUsers[keys[2]][Index]}",
                    "{self.buffDataUsers[keys[3]][Index]}",
                    {self.buffDataUsers[keys[4]][Index] if self.buffDataUsers[keys[4]][Index] != '' else '0'},
                    {self.buffDataUsers[keys[5]][Index] if self.buffDataUsers[keys[5]][Index] != '' else '0'},
                    "{self.buffDataUsers[keys[6]][Index]}")''')

        if returnSearch:
            self.Search = True
            self.init_users_table()

    def save_data_data(self):
        keys = list(self.buffDataData.keys())
        for keyIndex in range(len(keys)):
            key = keys[keyIndex]
            self.dataData[key] = [self.table_Data.item(row, keyIndex).text() for row in range(self.table_Data.rowCount())]

        self.buffDataData = copy.deepcopy(self.dataData)

        execute('''DELETE FROM Data WHERE 1 = 1''')

        for Index in range(len(self.buffDataData['ID'])):
            print(f'''INSERT INTO Data ({", ".join(self.buffDataData.keys())}) VALUES ("{self.buffDataData['ID'][Index]}", "{self.buffDataData['Value'][Index]}")''')
            execute(f'''INSERT INTO Data ({", ".join(self.buffDataData.keys())}) VALUES ("{self.buffDataData['ID'][Index]}", "{self.buffDataData['Value'][Index]}")''')

        data = GetRaw('''SELECT Value FROM Data WHERE `ID` LIKE "s%"''')

        SICELS = [str(x[0]).split("|")[0] for x in data]
        print("Data data saved:", self.buffDataData)

    def reset_data(self):
        print('reset data')
        self.buffDataData = copy.deepcopy(self.dataData)
        self.init_data_table()

def admin_mode():
    global exit_
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    app.exec()
    exit_ = True
    

if __name__ == "__main__":
    threading.Thread(target=camera_loader, daemon=True, name='Camera').start()
    while not camReady:
        print("Админ ожидает камеру...")
        time.sleep(0.2)
    admin_mode()
