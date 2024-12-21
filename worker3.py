import multiprocessing
import dlib
import settings
import threading
import db
import time
import cv2
import numpy as np
import struct

MyPrint = []
detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
face_rec_model = dlib.face_recognition_model_v1('dlib_face_recognition_resnet_model_v1.dat')
Verived_global = {"ID": -1, "Name": "F", "Path": "F", "Verifed": True}
Users = []
frame_encodings = []


# Определение расстояния до лица
def get_face_distance(face_rect, frame_width, known_face_width=0.20):
    """
    Вычисляет расстояние до лица на основе его ширины.
    
    :param face_rect: Прямоугольник, описывающий лицо.
    :param frame_width: Ширина кадра в пикселях.
    :param known_face_width: Известная ширина лица в метрах (по умолчанию 0.20 м).
    :return: Расстояние до лица в метрах.
    """
    face_width_in_pixels = face_rect.width()
    focal_length = (frame_width * known_face_width) / face_width_in_pixels
    distance = known_face_width * focal_length / face_width_in_pixels
    return distance

# Определение смазанности изображения
def is_blurry(image):
    """
    Определяет, является ли изображение смазанным.
    :param image: Изображение в формате BGR.
    :return: True, если изображение смазано, иначе False.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var < settings.BLUR_THRESHOLD

def enhance_contrast(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)  # Переводим изображение в LAB-цветовое пространство
    l, a, b = cv2.split(lab)  # Разделяем на каналы

    # Применяем CLAHE (адаптивное выравнивание гистограммы) к L-каналу
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)

    # Объединяем каналы обратно
    lab = cv2.merge((cl, a, b))
    enhanced_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)  # Возвращаемся в BGR
    return enhanced_image

# Проверка угла наклона лица
def check_face_angle(landmarks):
    """
    Проверяет, находится ли лицо под допустимым углом.
    :param landmarks: Объект с ключевыми точками лица.
    :return: True, если угол наклона лица допустим, иначе False.
    """
    left_eye = landmarks.part(36)
    right_eye = landmarks.part(45)
    eye_delta_y = right_eye.y - left_eye.y
    eye_delta_x = right_eye.x - left_eye.x
    angle = np.degrees(np.arctan2(eye_delta_y, eye_delta_x))
    return abs(angle) < settings.DERREES



# Функция для вывода сообщений
def PrintMy():
    global MyPrint
    while True:
        if len(MyPrint) > 0:
            print(MyPrint[0])
            MyPrint.pop(0)



# Отрисовка ключевых точек на лице
def draw_face_landmarks(image, detections):
    """
    Отображает на изображении ключевые точки лица.

    :param image: Изображение в формате BGR.
    :param detections: Объект, содержащий координаты обнаруженных лиц.
    :return: Изображение с нарисованными точками.
    """
    for face in detections:
        x, y, w, h = face.left(), face.top(), face.width(), face.height()
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
        shape = shape_predictor(image, face)
        for i in range(0, 68):
            x = shape.part(i).x
            y = shape.part(i).y
            cv2.circle(image, (x, y), 1, (255, 0, 0), -1)
        points = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
        cv2.line(image, points[17], points[21], (255, 0, 0), 1)  # левая бровь
        cv2.line(image, points[22], points[26], (255, 0, 0), 1)  # правая бровь
        cv2.line(image, points[36], points[39], (255, 0, 0), 1)  # левый глаз
        cv2.line(image, points[42], points[45], (255, 0, 0), 1)  # правый глаз
        cv2.line(image, points[48], points[54], (255, 0, 0), 1)  # рот
    return image




# Извлечение кодировок лица
def extract_face_encoding(image, draw_landmarks=False):
    global detections
    # Обнаружение лиц
    detections = detector(image, 1)
    
    # Если лиц не обнаружено, возвращаем пустой список и оригинальное изображение
    if len(detections) == 0:
        return [], image

    # Рисуем рамки и ключевые точки, если draw_landmarks = True
    if draw_landmarks:
        image = draw_face_landmarks(image, detections)

    # Для каждого лица извлекаем дескрипторы
    encodings = []
    for det in detections:
        shape = shape_predictor(image, det)
        face_descriptor = face_rec_model.compute_face_descriptor(image, shape)
        encodings.append(np.array(face_descriptor))
    
    return encodings, image # Возвращаем кодировки и изображение с ключевыми точками (если они есть)




# Создание геометрий лиц для всех пользователей
def CreateGeometrics(HARDUPDATE=False):
    """
    Создает или обновляет кодировки лиц для пользователей из базы данных.
    :param HARDUPDATE: Если True, выполняется принудительное обновление кодировок.
    """
    global Users
    Users = db.get_users()
    settings.fprint("ПОЛУЧЕН ЗАПРОС НА СОЗДАНИЕ ГЕОМЕТРИЙ", type="C5 T1 T3")
    startTime = time.time()
    if HARDUPDATE:
        settings.fprint("ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ", type="C1 T1 T3")
    
    for User in Users:
        settings.fprint("Обработка ", end='', type="C6")
        settings.fprint(str(User["PhotoPath"]), type="T2")
        
        if User["FaceEncoding"] == "" or HARDUPDATE:
            img = cv2.imread(User["PhotoPath"])
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = extract_face_encoding(img)
            
            if len(encodings) == 0:
                settings.fprint("Не удалось извлечь лицо. Пропуск...", type="C1 T2")
                db.update_user_code(User["ID"], "")
                continue
            else:
                encoding_str = "|".join(map(str, encodings[0][0]))
                settings.fprint("Лицо распознано успешно, сохранение...", type="C3")
                db.update_user_code(User["ID"], encoding_str)
        else:
            settings.fprint("В обновлении не нуждается", type="C3")

    Users = db.get_users()
    settings.fprint(f"ЗАПРОС НА СОЗДАНИЕ ГЕОМЕТРИЙ ОБРАБОТАН ЗА {time.time() - startTime} секунд", type="C3 T1 T3")




# Создание потоков для проверки лиц
def Create_Tread():
    """
    Создает потоки для многопоточной обработки лиц.
    """
    global TotalTreads
    Number = settings.THREAD_COUNT
    TotalTreads = Number
    print("Go printer")
    threading.Thread(target=PrintMy, name=f"Printer", daemon=True).start()
    print(f"strat {Number} Thread")
    for i in range(Number):
        threading.Thread(target=Tread_new, args=[i], name=f"Photo verifed {i}", daemon=True).start()
    print(f"strat {Number} Thread -> OK")
lock = threading.Lock()





# Основная функция для обработки кадра
# Основная функция для обработки кадра
def Qest(Frame):
    global Verived_global, frame_encodings, Users, MyPrint, detections
    enhanced_frame = enhance_contrast(Frame)
    settings.fprint("ЗАПРОС ПОЛУЧЕН", type="C5 T1 T3")
    start_time = time.time()
            # Проверка на смазанность
    if is_blurry(Frame):
        settings.fprint("Изображение смазано, возврат None", type="C1 T1 T2")
        return None

    with lock:
        frame_encodings, Frame_with_landmarks = extract_face_encoding(enhanced_frame, draw_landmarks=True)  # Передаем True, чтобы рисовать
        # Проверка на смазанность
        if is_blurry(Frame):
            settings.fprint("Изображение смазано, возврат None", type="C1 T1 T2")
            return None
    if len(frame_encodings) > 0:
        MyPrint.append("Лица закодированы, передача в потоки...")

        det = detections[0]
        frame_height, frame_width = Frame.shape[:2]
        distance1 = get_face_distance(det, frame_width)
        distance1 *= 200
        if distance1 > 0.3:  # Пример порога расстояния в 10 метров
            settings.fprint(f"Пользователь слишком далеко {distance1}, возврат None", type="C1 T1 T2")
            return None
        

        shape = shape_predictor(Frame, det)
        if not check_face_angle(shape):
            settings.fprint("Угол наклона лица недопустим, возврат None", type="C1 T1 T2")
            return None

        
        # Отображаем изображение с рамками и ключевыми точками
        cv2.imshow('Detected Faces', Frame_with_landmarks)
        cv2.waitKey(1)

        Verived_global = {"ID": -1, "Name": "F", "Verifed": False}
        while not Verived_global["Verifed"]:
            pass
        time.sleep(0.2)
        settings.fprint("Пользователь верифицирован: ", type="C3 T1 T3", end='')
        settings.fprint(str(Verived_global["ID"]), " ", str(Verived_global["Name"]))
        total_time = time.time() - start_time
        settings.fprint(f"Обработка изображений завершена за {total_time:.2f} секунд.", type="C6")
        time.sleep(0.2)
        if Verived_global["ID"] == -1:
            return None
        return Verived_global["ID"]
    else:
        settings.fprint("Лица не обнаружены, возврат None", type="C1 T1 T2")
        return None





def Tread_new(Number):
    global TotalTreads, frame_encodings, Verived_global, MyPrint, Users
    MyPrint.append(f"Поток {Number}, запущен")
    while True:
        if not Verived_global["Verifed"]:
            frame_encodingsLocal = frame_encodings.copy()
            for i in range(Number, len(Users), TotalTreads):
                if Verived_global["Verifed"]:
                    break
                User = Users[i]
                MyPrint.append(f"Поток {Number}, сравнение с " + str(User["PhotoPath"]) + "\n")

                with lock:
                    save = str(User["FaceEncoding"])
                if save != "" and len(frame_encodingsLocal) > 0:
                    Point1 = np.array([np.array(list(map(float, save.split("|"))))])
                    distance = np.linalg.norm(Point1 - frame_encodingsLocal, axis=1)
                    result = distance <= settings.TOLERANCE
                    distancea = round(distance[0], 3)
                    print("\n", distancea)
                    
                    if result[0]:
                        MyPrint.append(f"Поток {Number}, ОК")
                        Verived_global["ID"] = User["ID"]
                        Verived_global["Name"] = User["Name"]
                        Verived_global["Verifed"] = True
                        break
                    else:
                        if i == len(Users) - 1:
                            MyPrint.append(f"Поток {Number}, пользователь не зарегистрирован в системе")
                            Verived_global["ID"] = -1
                            Verived_global["Name"] = "F"
                            Verived_global["Verifed"] = True
                            break
