import cv2
import threading
import time
import worker3 as worker3
from datetime import datetime
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout

import os
from db import GetData, dataToExcel, WriteData
from settings import HARDUPDATE, CAMERA_INDEX, fprint, SOUND_PATH, DYBLS, MIN_TIME, EXCEL_LOG_PATH
from audio import record_and_recognize_audio, play, noise  # Импортируем функцию для распознавания речи
from design import admin_mode

class poromt_input(QDialog):
    def __init__(self, label_text="Введите текст"):
        super().__init__()

        self.setWindowTitle("Введите текст")
        self.ready = False

        # Создание основного макета
        self.layout = QVBoxLayout()

        # Метка с текстом
        self.label = QLabel(label_text)
        self.layout.addWidget(self.label)

        # Поле ввода текста
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Введите текст здесь")
        self.layout.addWidget(self.input_field)

        # Макет для кнопок
        self.button_layout = QHBoxLayout()

        # Кнопка OK
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.button_layout.addWidget(self.ok_button)

        # Кнопка Назад
        self.cancel_button = QPushButton("Назад")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)

        # Добавление макета кнопок в основной макет
        self.layout.addLayout(self.button_layout)

        # Установка основного макета для диалога
        self.setLayout(self.layout)

    def on_ok_clicked(self):
        self.ready = True
        self.accept()

    def get_text(self):
        if self.ready:
            return self.input_field.text()
        return None
    
data = {}  
camReady = False
frame = None
inp = ''
busy = False
mode = 'Std'
ret = False
sircls = {}
data = {
    "Имя":[],
    "Направление":[],
    "Время":[],
    "Дата":[]
}

def consolLoad():
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    global inp, busy, mode
    while True:
        dialog = poromt_input("Пожалуйста, введите режим")
        if dialog.exec():
            inp = dialog.get_text()
            if 'обнов' in inp.lower():
                print('Обнова, люди')
                worker3.CreateGeometrics(True)
                buffClass()
            
            elif "админ" in inp.lower():
                print("Запуск админ...")
                if mode == 'Std':
                    mode = 'Admin'
                    time.sleep(1)
                    os.system('"C:/Program Files/Python311/python.exe" c:/prog/SASA/design.py')
                    mode = 'Std'
            

            elif "выход" in inp.lower():
                print("Выход...")
                fprint("BYE", type="C6 T1 BANER")
                mode = 'Exit'
                exit(0)
            
        else:
            print("Действие отменено")

def LogExel():
    global data
    while True:
        if data != {"Имя":[], "Направление":[], "Время":[], "Дата":[]}:
            print('Write to exel')
            dataToExcel(data, EXCEL_LOG_PATH, "over")
            data = {"Имя":[], "Направление":[], "Время":[], "Дата":[]}

# Функция для захвата изображения с камеры
def camera_loader():
    global frame, camReady, ret, mode
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    while True:
        if mode == 'Std':
            ret, frame = camera.read()
            if ret:
                cv2.imshow('Cam', frame)
                cv2.waitKey(1)
                if not camReady:
                    camReady = True
                    print("Камера готова к работе")
        else:
            camera.release()
            camReady = False
            cv2.destroyAllWindows()
            while mode == 'Admin':
                time.sleep(0.2)
            camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

def buffClass():
    print('Получен запрос на буфферизацию классов')
    i = 1
    global sircls
    while GetData(2, "Value", f"s{i}") != []:
        checkSps = str(GetData(2, "Value", f"s{i}")[0][0]).lower().split('|')
        sircls[i] = checkSps
        i += 1

def getClassID2(klass:str):
    global sircls
    klass = klass.lower()
    print(f"Ищем класс: {klass}")
    for key in sircls.keys():
        for checkWord in sircls[key]:
            # print('сравнение с', checkWord)
            if checkWord in klass:
                print('ОК')
                return key
    return -1

def getClassID(klass=""):
    i = 1
    klass = klass.title()
    print(f"Ищем класс: {klass}")  # Отладочное сообщение
    while GetData(2, "Value", f"s{i}") != []:
        checkSps = str(GetData(2, "Value", f"s{i}")[0][0]).split()
        print(f"Сравним с: {checkSps}")  # Отладочное сообщение
        for checkword in checkSps:
            print(f"Сравниваем с: {checkword}")
            if checkword in klass:
                print(f"Найдено совпадение: {checkword} с ID {i}")  # Отладочное сообщение
                return i
        i += 1
    print("Класс не найден")  # Отладочное сообщение
    return -1

def main():
    global camReady, frame, inp, busy, ret, sircls, data, mode
    print("Запуск камеры и writer-а...")
    noise()
    threading.Thread(target=camera_loader, daemon=True, name='Camera').start()
    threading.Thread(target=LogExel, daemon=True, name='writer').start()
    buffClass()
    
    
    while True:
        if mode == 'Std' and not busy:
            while not camReady:
                print("Ожидание камеры...")
                time.sleep(0.2)
            busy = True
            if ret:
                ID = worker3.Qest(frame)

                if ID:
                    cur_dt = datetime.now()
                    lTimeMin = GetData(1, "PrevTime", ID)[0][0]
                    lDay = GetData(1, "PrevDay", ID)[0][0]
                    curDay = cur_dt.month * 100 + cur_dt.day
                    curMin = cur_dt.hour * 100 + cur_dt.minute
                    # NamePaul = GetData(1, "Name", ID)[0][0]
                    print(curDay, lDay)
                    print(curMin, lTimeMin)
                    if (curDay - lDay == 0 and abs(curMin - lTimeMin) < MIN_TIME or not DYBLS):
            
                        print("Голосовой ввод")
                        
                        play(SOUND_PATH + 'hello.mp3')
                        classID = -1
                        while classID == -1:
                            voice_input = record_and_recognize_audio()
                            if voice_input:
                                fprint(f"Распознана голосовая команда: {voice_input}", type="C6")
                                classID = getClassID2(voice_input)
                                #print("Распознанный класс:", classID)
                                if classID != -1:
                                    sircl = sircls[classID][0]
                                    cur_dt = datetime.now()
                                    day = f"{cur_dt.day:02}.{cur_dt.month:02}.{cur_dt.year:04}"
                                    Time = f"{cur_dt.hour:02}:{cur_dt.minute:02}"
                                    Name = GetData(1, "Name", ID)[0][0]
                                    data["Имя"].append(Name)
                                    data["Направление"].append(sircl)
                                    data["Время"].append(Time)
                                    data["Дата"].append(day)
                                    print(data)
                                    fprint("DA", type="C3 T1 BANER")
                                    play(SOUND_PATH + 'succses2.mp3')
                                    break
                                else:
                                    play(SOUND_PATH + 'ERR_use.mp3')
                    else:
                        fprint("ДУБЛЕЙ ИГНОРИРУЕМ", type="C1 T1")
                else:
                    print("Чела нет на фото")
            busy = False
            time.sleep(0.0002)
        elif mode == 'Exit':
            exit(0)

if __name__ == '__main__':
    worker3.CreateGeometrics(HARDUPDATE)
    worker3.Create_Tread()
    threading.Thread(target=consolLoad, daemon=True).start()
    main()

