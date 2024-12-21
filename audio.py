import speech_recognition as sr
import time
import pygame
from mutagen.mp3 import MP3
from settings import SOUND_PATH, DURATION, fprint
recognizer = sr.Recognizer()
microphone = sr.Microphone()
# Функция для записи и распознавания речи

def noise():
    print("Настройка шумоподавления...")
    with microphone:
        recognizer.adjust_for_ambient_noise(microphone, DURATION)

def record_and_recognize_audio():
    with microphone:
        try:
            print("Слушаю...")
            audio = recognizer.listen(microphone, timeout=5)
        except sr.WaitTimeoutError:
            print("Проверьте микрофон!")
            play(SOUND_PATH + 'check_micro.mp3')
            return None

        try:
            print("Распознаю речь...")
            text = recognizer.recognize_google(audio, language="ru-RU")
            print(f"Распознано: {text}")
            return text.lower()
        except sr.UnknownValueError:
            print("Речь не распознана")
        except sr.RequestError:
            print("Ошибка соединения с интернетом")


def play(PATH):
    pygame.mixer.music.load(PATH)
    pygame.mixer.music.play()
    audio = MP3(PATH)
    time.sleep(audio.info.length)
