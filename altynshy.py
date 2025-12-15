from PIL import Image, ImageTk
import time
import requests
import numpy as np
import sounddevice as sd
import json
import vosk
import webbrowser
import tkinter as tk
from tkinter import ttk
import threading
from PIL import Image, ImageDraw, ImageFont
import requests
from PIL import Image, ImageTk
import io
import re
import os
import base64
import urllib.parse
import subprocess
import shutil
from dotenv import load_dotenv
import google.generativeai as genai

# Загружаем переменные из .env
load_dotenv()

# API ключи из .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-image-preview")
GEMINI_API_VERSION = os.getenv("GEMINI_API_VERSION", "v1beta")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")
DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")
VOSK_MODEL_PATH = r"C:\Users\As\Desktop\Nur_assist\vosk-model-kz-0.15"

# Настройка Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

model = vosk.Model(VOSK_MODEL_PATH)
awaiting_confirmation = False
assistant_active = False
assistant_thread = None
listening_thread = None
pending_image_request = False
generated_image_data = None
selected_voice = "madi"
is_listening = True  # Флаг для постоянного прослушивания


def get_yandex_voice_response(text):
    url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "text": text,
        "lang": "kk-KZ",
        "voice": selected_voice,
        "format": "lpcm",
        "sampleRateHertz": 48000
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        audio_data = np.frombuffer(response.content, dtype=np.int16)
        sd.play(audio_data, samplerate=48000)
        sd.wait()
    else:
        print("Аудио қатесі:", response.text)

def update_user_dialog(text, tag=None):
    """Обновляет диалог с красивым форматированием сообщений"""
    if tag:
        # Добавляем отступы для визуального разделения
        user_dialog.insert(tk.END, "\n", tag)
        user_dialog.insert(tk.END, text + "\n", tag)
        user_dialog.insert(tk.END, "\n", tag)
    else:
        user_dialog.insert(tk.END, text + "\n")
    user_dialog.see(tk.END)
    
    # Автоматическая прокрутка вниз
    window.update_idletasks()

weather_conditions_kk = {
    200: 'Найзағайлы жеңіл жаңбыр',
    201: 'Найзағайлы жаңбыр',
    202: 'Найзағайлы күшті жаңбыр',
    210: 'Жеңіл найзағай',
    211: 'Найзағай',
    212: 'Күшті найзағай',
    221: 'Күшті найзағай',
    230: 'Найзағайлы жеңіл жаңбыр',
    231: 'Найзағайлы жаңбыр',
    232: 'Найзағайлы күшті жаңбыр',
    300: 'Жеңіл жаңбыр себелеу',
    301: 'Жаңбыр себелеу',
    302: 'Күшті жаңбыр себелеу',
    310: 'Жеңіл жаңбырлы себелеу',
    311: 'Жаңбырлы себелеу',
    312: 'Күшті жаңбырлы себелеу',
    313: 'Жаңбыр және себелеу',
    314: 'Күшті жаңбыр және себелеу',
    321: 'Жаңбырлы себелеу',
    500: 'Жеңіл жаңбыр',
    501: 'Орташа жаңбыр',
    502: 'Күшті жаңбыр',
    503: 'Өте күшті жаңбыр',
    504: 'Өте қатты жаңбыр',
    511: 'Мұздай жаңбыр',
    520: 'Жеңіл қатты жаңбыр',
    521: 'Қатты жаңбыр',
    522: 'Күшті қатты жаңбыр',
    531: 'Кездейсоқ жаңбыр',
    600: 'Жеңіл қар',
    601: 'Қар',
    602: 'Күшті қар',
    611: 'Жылбысқы',
    612: 'Жеңіл жылбысқы',
    613: 'Күшті жылбысқы',
    615: 'Жеңіл жаңбыр мен қар',
    616: 'Жаңбыр мен қар',
    620: 'Жеңіл қатты қар',
    621: 'Қатты қар',
    622: 'Күшті қатты қар',
    701: 'Тұман',
    711: 'Түтін',
    721: 'Тұман',
    731: 'Құмды құйын',
    741: 'Тұман',
    751: 'Құм',
    761: 'Шаң',
    762: 'Вулканды күл',
    771: 'Кенеттен жел',
    781: 'Торнадо',
    800: 'Ашық аспан',
    801: 'Аз бұлтты',
    802: 'Орташа бұлтты',
    803: 'Бұлыңғыр',
    804: 'Қою бұлтты',
}
weather_emojis = {
    200: "⛈️", 201: "⛈️", 202: "⛈️", 210: "⚡", 211: "⚡", 212: "⚡", 221: "🌩️", 230: "🌦️", 231: "🌦️", 232: "🌦️",
    300: "🌧️", 301: "🌧️", 302: "🌧️", 310: "🌧️", 311: "🌧️", 312: "🌧️", 313: "🌧️", 314: "🌧️", 321: "🌧️",
    500: "🌦️", 501: "🌧️", 502: "🌧️", 503: "🌧️", 504: "🌧️", 511: "🌧️❄️", 520: "🌦️", 521: "🌧️", 522: "🌧️", 531: "🌧️",
    600: "🌨️", 601: "🌨️", 602: "❄️", 611: "🌨️", 612: "🌨️", 613: "🌨️", 615: "🌨️🌧️", 616: "🌨️🌧️", 620: "❄️", 621: "❄️", 622: "❄️",
    701: "🌫️", 711: "🌫️", 721: "🌫️", 731: "🌪️", 741: "🌫️", 751: "🌫️", 761: "🌫️", 762: "🌋", 771: "💨", 781: "🌪️",
    800: "☀️", 801: "🌤️", 802: "⛅", 803: "☁️", 804: "☁️"
}

kazakh_phrases = [
    "Сәлеметсіз бе? - Здравствуйте",
    "Қалыңыз қалай? - Как ваши дела?",
    "Рақмет - Спасибо",
    "Кешіріңіз - Извините",
    "Қайырлы таң - Доброе утро",
    "Қайырлы күн - Добрый день",
    "Қайырлы кеш - Добрый вечер",
    "Сау болыңыз - До свидания"
]

recipes = {
    "бешбармақ": "Бешбармақ рецепті:\n1. Етті қайнатып пісіріңіз.\n2. Қамыр дайындаңыз.\n3. Қамырды жайып, кесіңіз.\n4. Қамырды еттің сорпасында пісіріңіз.\n5. Ет пен қамырды бірге беріңіз.",
    "бауырсақ": "Бауырсақ рецепті:\n1. Ұн, ашытқы, сүт, қант және тұзды араластырыңыз.\n2. Қамырды илеп, көтерілуге қалдырыңыз.\n3. Қамырды бөліктерге бөліп, пішін беріңіз.\n4. Қайнаған майда қуырыңыз."
}

heroes = {
    "абылай хан": "Абылай хан - қазақтың ұлы хандарының бірі, қазақ халқының тәуелсіздігі үшін күрескен.",
    "бауыржан момышұлы": "Бауыржан Момышұлы - Ұлы Отан соғысының батыры, қазақтың атақты қолбасшысы."
}

holidays = [
    "22 наурыз - Наурыз мейрамы",
    "1 мамыр - Қазақстан халықтарының бірлігі күні",
    "9 мамыр - Жеңіс күні",
    "6 шілде - Астана күні",
    "30 тамыз - Конституция күні",
    "16 желтоқсан - Тәуелсіздік күні"
]

def create_weather_image(city, temperature, description, emoji):
    img = Image.new("RGB", (400, 40), color=(52, 52, 52))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 14)
    text = f"{city} {emoji} {temperature}°C - {description}"
    draw.text((10, 10), text, font=font, fill="white")
    return img

def get_weather_emoji(condition_id):
    return weather_emojis.get(condition_id, "")

def get_weather_in_almaty():
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Almaty&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        condition_id = weather_data["weather"][0]["id"]
        description = weather_conditions_kk.get(condition_id, "Ауа райы туралы мәлімет жоқ")
        emoji = get_weather_emoji(condition_id)
        temperature = int(weather_data["main"]["temp"])
        weather_image = create_weather_image("Алматы", temperature, description, emoji)
        display_weather_image_in_dialog(weather_image)
        weather_text = f"Алматы қаласындағы ауа райы: {description} {emoji}, температура {temperature} градус"
        return weather_text
    else:
        return "Кешіріңіз, ауа райын ала алмадым."

def display_weather_image_in_dialog(weather_image):
    # Инициализируем список изображений если его нет
    if not hasattr(user_dialog, 'images'):
        user_dialog.images = []
    
    # Создаем PhotoImage и сохраняем ссылку ДО вставки
    img_tk = ImageTk.PhotoImage(weather_image)
    user_dialog.images.append(img_tk)  # Сохраняем ПЕРЕД вставкой
    
    # Вставляем изображение
    user_dialog.image_create(tk.END, image=img_tk)
    user_dialog.insert(tk.END, "\n")

def recognize_speech(timeout_seconds=None):
    """Распознает речь с опциональным таймаутом"""
    global assistant_active
    window.after(0, start_gif_animation)
    recognizer = vosk.KaldiRecognizer(model, 16000)
    audio = sd.InputStream(samplerate=16000, channels=1, dtype='int16')
    
    start_time = time.time()
    with audio:
        print("Айтыңыз...")
        audio.start()
        # Используем is_listening вместо assistant_active для постоянного прослушивания
        while is_listening:
            if timeout_seconds and (time.time() - start_time) > timeout_seconds:
                window.after(0, stop_gif_animation)
                return ""
            
            data, _ = audio.read(4000)
            data = data.flatten().tobytes()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                window.after(0, stop_gif_animation)
                recognized_text = result.get("text", "").lower()
                if recognized_text:
                    update_user_dialog(f"Сіз: {recognized_text}", 'user_message')
                    return recognized_text
    window.after(0, stop_gif_animation)
    return ""

def listen_for_activation():
    """Постоянно слушает активационное слово 'Felix'"""
    global is_listening, assistant_active
    
    recognizer = vosk.KaldiRecognizer(model, 16000)
    audio = sd.InputStream(samplerate=16000, channels=1, dtype='int16')
    
    with audio:
        audio.start()
        while is_listening:
            try:
                data, _ = audio.read(4000)
                data = data.flatten().tobytes()
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").lower()
                    
                    # Проверяем, содержит ли текст активационное слово
                    if "felix" in text or "феликс" in text:
                        window.after(0, lambda: update_user_dialog("Felix: Сізді тыңдап тұрмын... 🎤", 'assistant_message'))
                        window.after(0, start_gif_animation)
                        
                        # Извлекаем команду из текста (после слова Felix)
                        command = text
                        for activation_word in ["felix", "феликс"]:
                            if activation_word in command:
                                # Берем текст после активационного слова
                                parts = command.split(activation_word, 1)
                                if len(parts) > 1:
                                    command = parts[1].strip()
                                else:
                                    command = ""
                                break
                        
                        if command:
                            # Если команда уже есть в тексте, обрабатываем сразу
                            window.after(0, stop_gif_animation)
                            process_voice_command(command)
                        else:
                            # Если команды нет, ждем дополнительный ввод (таймаут 3 секунды)
                            time.sleep(0.5)  # Небольшая задержка для лучшего распознавания
                            command = recognize_speech(timeout_seconds=3)
                            
                            if command:
                                window.after(0, stop_gif_animation)
                                process_voice_command(command)
                            else:
                                window.after(0, stop_gif_animation)
                                window.after(0, lambda: update_user_dialog("Felix: Кешіріңіз, естілмеді.", 'assistant_message'))
                
                # Также проверяем частичное распознавание для более быстрой реакции
                partial = recognizer.PartialResult()
                if partial:
                    partial_text = json.loads(partial).get("partial", "").lower()
                    if "felix" in partial_text or "феликс" in partial_text:
                        window.after(0, start_gif_animation)
                        
            except Exception as e:
                print(f"Ошибка при прослушивании: {e}")
                time.sleep(0.1)

def open_free_chatgpt():
    webbrowser.open("https://chat.openai.com/?q=Сәлем,%20маған%20қазақ%20тіліндегі%20жауаптар%20қажет")

def launch_spotify():
    """Запускает Spotify"""
    try:
        # Пробуем разные пути к Spotify
        spotify_paths = [
            os.path.expanduser("~/AppData/Roaming/Spotify/Spotify.exe"),
            "C:/Users/%USERNAME%/AppData/Roaming/Spotify/Spotify.exe",
            "spotify.exe",  # Если в PATH
        ]
        
        for path in spotify_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                subprocess.Popen([expanded_path])
                update_user_dialog("Felix: Spotify ашылуда...", 'assistant_message')
                get_yandex_voice_response("Spotify ашылуда")
                return
        
        # Если не нашли, пробуем через start
        subprocess.Popen(["start", "spotify:"], shell=True)
        update_user_dialog("Felix: Spotify ашылуда...", 'assistant_message')
        get_yandex_voice_response("Spotify ашылуда")
    except Exception as e:
        error_msg = f"Spotify ашу мүмкін болмады: {str(e)}"
        update_user_dialog(f"Felix: {error_msg}", 'assistant_message')
        print(f"Spotify ошибка: {e}")

def search_spotify(query):
    """Ищет и воспроизводит музыку в Spotify"""
    try:
        # Кодируем запрос для URL
        encoded_query = urllib.parse.quote(query)
        
        # Используем Spotify URI для поиска
        spotify_uri = f"spotify:search:{query}"
        
        # Пробуем открыть через URI
        try:
            os.startfile(spotify_uri)
            response = f"Spotify-та '{query}' ізделуде..."
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
        except:
            # Если URI не работает, открываем веб-версию
            spotify_url = f"https://open.spotify.com/search/{encoded_query}"
            webbrowser.open(spotify_url)
            response = f"Spotify-та '{query}' ізделуде..."
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
    except Exception as e:
        error_msg = f"Spotify-та іздеу мүмкін болмады: {str(e)}"
        update_user_dialog(f"Felix: {error_msg}", 'assistant_message')
        print(f"Spotify search ошибка: {e}")

def search_yandex(query):
    """Выполняет поиск в Яндексе"""
    try:
        # Кодируем запрос для URL
        encoded_query = urllib.parse.quote(query)
        yandex_url = f"https://yandex.kz/search/?text={encoded_query}"
        
        webbrowser.open(yandex_url)
        response = f"Яндекс-те '{query}' ізделуде..."
        update_user_dialog(f"Felix: {response}", 'assistant_message')
        get_yandex_voice_response(response)
    except Exception as e:
        error_msg = f"Яндекс-те іздеу мүмкін болмады: {str(e)}"
        update_user_dialog(f"Felix: {error_msg}", 'assistant_message')
        print(f"Yandex search ошибка: {e}")

def launch_youtube():
    """Открывает YouTube"""
    try:
        webbrowser.open("https://www.youtube.com")
        update_user_dialog("Felix: YouTube ашылуда...", 'assistant_message')
        get_yandex_voice_response("YouTube ашылуда")
    except Exception as e:
        error_msg = f"YouTube ашу мүмкін болмады: {str(e)}"
        update_user_dialog(f"Felix: {error_msg}", 'assistant_message')
        print(f"YouTube ошибка: {e}")

def launch_steam():
    """Запускает Steam"""
    try:
        # Пробуем разные пути к Steam
        steam_paths = [
            "C:/Program Files (x86)/Steam/steam.exe",
            "C:/Program Files/Steam/steam.exe",
            os.path.expanduser("~/Desktop/Steam.lnk"),
            "steam://",  # URI протокол
        ]
        
        for path in steam_paths:
            if path.startswith("steam://"):
                os.startfile(path)
                update_user_dialog("Felix: Steam ашылуда...", 'assistant_message')
                get_yandex_voice_response("Steam ашылуда")
                return
            elif os.path.exists(path):
                subprocess.Popen([path])
                update_user_dialog("Felix: Steam ашылуда...", 'assistant_message')
                get_yandex_voice_response("Steam ашылуда")
                return
        
        # Если не нашли, пробуем через start
        subprocess.Popen(["start", "steam://"], shell=True)
        update_user_dialog("Felix: Steam ашылуда...", 'assistant_message')
        get_yandex_voice_response("Steam ашылуда")
    except Exception as e:
        error_msg = f"Steam ашу мүмкін болмады: {str(e)}"
        update_user_dialog(f"Felix: {error_msg}", 'assistant_message')
        print(f"Steam ошибка: {e}")

def launch_chrome():
    """Запускает Google Chrome"""
    try:
        # Пробуем разные пути к Chrome
        chrome_paths = [
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            os.path.expanduser("~/AppData/Local/Google/Chrome/Application/chrome.exe"),
            "chrome.exe",  # Если в PATH
        ]
        
        for path in chrome_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                subprocess.Popen([expanded_path])
                update_user_dialog("Felix: Chrome ашылуда...", 'assistant_message')
                get_yandex_voice_response("Chrome ашылуда")
                return
        
        # Если не нашли, пробуем через start
        subprocess.Popen(["start", "chrome"], shell=True)
        update_user_dialog("Felix: Chrome ашылуда...", 'assistant_message')
        get_yandex_voice_response("Chrome ашылуда")
    except Exception as e:
        error_msg = f"Chrome ашу мүмкін болмады: {str(e)}"
        update_user_dialog(f"Felix: {error_msg}", 'assistant_message')
        print(f"Chrome ошибка: {e}")

def get_gemini_response(prompt):
    """Получает ответ от Gemini на казахском языке"""
    try:
        if not GEMINI_API_KEY:
            return "Кешіріңіз, Gemini API кілті орнатылмаған."
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        system_prompt = "Сіз Felix - қазақ тіліндегі AI көмекші. Барлық жауаптарды қазақ тілінде ғана беріңіз. Қысқа, нақты және пайдалы жауаптар беріңіз."
        
        full_prompt = f"{system_prompt}\n\nСұрақ: {prompt}\n\nЖауап:"
        response = model.generate_content(full_prompt)
        
        # Правильная обработка ответа Gemini
        if response and response.candidates:
            # Извлекаем текст из частей ответа
            text_parts = []
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
            
            if text_parts:
                return ' '.join(text_parts).strip()
        
        # Fallback на response.text если доступен
        try:
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
        except:
            pass
        
        return "Кешіріңіз, жауап ала алмадым."
    except Exception as e:
        print(f"Gemini қатесі: {e}")
        return f"Қате орын алды: {str(e)}"

def show_image_window(image, title="Сгенерированное изображение"):
    """Открывает изображение в отдельном окне"""
    img_window = tk.Toplevel(window)
    img_window.title(f"Сурет: {title}")
    img_window.configure(bg="#1E1E2E")
    
    # Вычисляем размер окна (максимум 800x600)
    img_width, img_height = image.size
    max_width, max_height = 800, 600
    
    if img_width > max_width or img_height > max_height:
        ratio = min(max_width / img_width, max_height / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    else:
        display_image = image
    
    # Создаем PhotoImage и сохраняем ссылку
    img_tk = ImageTk.PhotoImage(display_image)
    
    # Создаем Label с изображением
    img_label = tk.Label(img_window, image=img_tk, bg="#1E1E2E")
    img_label.image = img_tk  # Сохраняем ссылку!
    img_label.pack(padx=20, pady=20)
    
    # Кнопка закрытия
    close_btn = tk.Button(img_window, text="Жабу", command=img_window.destroy,
                         bg="#4A90E2", fg="white", font=("Segoe UI", 10, "bold"),
                         relief="flat", padx=20, pady=5, cursor="hand2")
    close_btn.pack(pady=10)
    
    # Центрируем окно
    img_window.update_idletasks()
    x = (img_window.winfo_screenwidth() // 2) - (img_window.winfo_width() // 2)
    y = (img_window.winfo_screenheight() // 2) - (img_window.winfo_height() // 2)
    img_window.geometry(f"+{x}+{y}")

def generate_image_with_gemini(prompt):
    """Генерирует изображение через различные API (с fallback)"""
    # Попытка 1: DeepAI (если есть Pro аккаунт)
    try:
        if DEEPAI_API_KEY:
            deepai_url = "https://api.deepai.org/api/text2img"
            headers = {"Api-Key": DEEPAI_API_KEY}
            data = {"text": prompt}
            
            print(f"Генерация изображения через DeepAI: {prompt}")
            response = requests.post(deepai_url, headers=headers, data=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if 'output_url' in result:
                    output_url = result['output_url']
                    img_response = requests.get(output_url, timeout=30)
                    if img_response.status_code == 200:
                        image = Image.open(io.BytesIO(img_response.content))
                        print(f"Изображение загружено через DeepAI: {image.size}")
                        return image, None
    except Exception as e:
        print(f"DeepAI ошибка: {e}")
    
    # Попытка 2: Hugging Face Inference API (бесплатный)
    try:
        print(f"Попытка генерации через Hugging Face: {prompt}")
        # Используем стабильную модель для генерации изображений
        hf_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        headers = {"Authorization": "Bearer hf_placeholder"}  # Можно использовать без токена для некоторых моделей
        
        # Переводим промпт на английский для лучшей работы модели
        prompt_en = prompt  # Можно добавить переводчик
        
        payload = {"inputs": prompt_en}
        response = requests.post(hf_url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            print(f"Изображение загружено через Hugging Face: {image.size}")
            return image, None
        elif response.status_code == 503:
            # Модель загружается, нужно подождать
            return None, "Модель жүктелуде, бірнеше секунд күтіп қайталап көріңіз."
    except Exception as e:
        print(f"Hugging Face ошибка: {e}")
    
    # Попытка 3: Pollinations AI (полностью бесплатный, без API ключа)
    try:
        print(f"Попытка генерации через Pollinations: {prompt}")
        # Pollinations API - бесплатный сервис
        pollinations_url = "https://image.pollinations.ai/prompt/"
        # Кодируем промпт в URL
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"{pollinations_url}{encoded_prompt}?width=512&height=512"
        
        response = requests.get(image_url, timeout=60)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            print(f"Изображение загружено через Pollinations: {image.size}")
            return image, None
    except Exception as e:
        print(f"Pollinations ошибка: {e}")
    
    # Если все методы не сработали
    return None, "Кешіріңіз, сурет жасай алмадым. DeepAI Pro аккаунт қажет немесе интернет байланысын тексеріңіз."

def ask_for_image_prompt():
    """Спрашивает у пользователя что генерировать на казахском"""
    response = "Қандай сурет жасағым келеді? Сипаттаманы айтыңыз немесе жаз."
    update_user_dialog(f"Felix: {response}", 'assistant_message')
    get_yandex_voice_response(response)
    
    # Создаем диалоговое окно для ввода текста
    dialog_window = tk.Toplevel(window)
    dialog_window.title("Сурет сипаттамасы")
    dialog_window.geometry("400x150")
    dialog_window.configure(bg="#2D2D44")
    dialog_window.transient(window)
    dialog_window.grab_set()
    
    tk.Label(dialog_window, text="Сурет сипаттамасын енгізіңіз:", 
             font=("Segoe UI", 11), fg="white", bg="#2D2D44").pack(pady=10)
    
    prompt_entry = tk.Entry(dialog_window, font=("Segoe UI", 11), width=40, 
                           bg="#3A3A55", fg="white", insertbackground="white")
    prompt_entry.pack(pady=10, padx=20)
    prompt_entry.focus()
    
    def generate_from_dialog():
        image_prompt = prompt_entry.get().strip()
        dialog_window.destroy()
        
        if not image_prompt:
            update_user_dialog("Felix: Сипаттама енгізілмеді.", 'assistant_message')
            return
        
        update_user_dialog(f"Сіз: {image_prompt}", 'user_message')
        
        # Генерируем изображение
        update_user_dialog("Felix: Сурет жасалуда, күте тұрыңыз...", 'assistant_message')
        window.update()  # Обновляем окно чтобы показать сообщение
        
        image, error = generate_image_with_gemini(image_prompt)
        
        if image:
            # Удаляем сообщение "Сурет жасалуда..."
            try:
                # Находим и удаляем последнее сообщение
                end_pos = user_dialog.index(tk.END)
                start_pos = user_dialog.search("Felix: Сурет жасалуда", "end-10l", "end", backwards=True)
                if start_pos:
                    user_dialog.delete(start_pos, end_pos + "-1c")
            except:
                pass
            
            # Показываем сообщение в диалоге
            response_msg = f"Felix: Әрине, міне сізге {image_prompt} суреті! Суретті көру үшін терезе ашылады.\n\n"
            user_dialog.insert(tk.END, response_msg, 'assistant_message')
            user_dialog.see(tk.END)
            window.update()
            
            # Открываем изображение в отдельном окне
            show_image_window(image, image_prompt)
            
            success_msg = "Сурет сәтті жасалды!"
            get_yandex_voice_response(success_msg)
        else:
            # Удаляем сообщение "Сурет жасалуда..."
            user_dialog.delete("end-2l", "end-1l")
            error_msg = error or "Сурет жасау мүмкін болмады."
            update_user_dialog(f"Felix: {error_msg}", 'assistant_message')
            get_yandex_voice_response(error_msg)
    
    tk.Button(dialog_window, text="Жасау", command=generate_from_dialog,
             bg="#4A90E2", fg="white", font=("Segoe UI", 10, "bold"),
             relief="flat", padx=20, pady=5, cursor="hand2").pack(pady=10)
    
    prompt_entry.bind("<Return>", lambda e: generate_from_dialog())

def extract_number(text):
    numbers = re.findall(r'\d+', text)
    if numbers:
        return float(numbers[0])
    else:
        return None

def process_request(event=None):
    global awaiting_confirmation
    prompt = text_input.get()
    
    # Проверяем, не является ли это placeholder текстом
    placeholder_text = "Сұрағыңызды енгізіңіз..."
    if not prompt or prompt == placeholder_text:
        return

    update_user_dialog(f"Сіз: {prompt}", 'user_message')
    text_input.delete(0, 'end')
    text_input.insert(0, placeholder_text)
    text_input.config(fg="#6B6B7B")  # text_muted color

    if awaiting_confirmation:
        awaiting_confirmation = False
        if "ия" in prompt.lower() or "иә" in prompt.lower():
            response = "Іздеу жүйесі ашылды."
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
            open_free_chatgpt()
        else:
            response = "Сұрағыңызға жауап бере алмадым."
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
        return

    if "атыңыз кім" in prompt or "как тебя зовут" in prompt:
        response = "Мен Felix. Менің басты жұмысым қолданушыға ыңғайлы және қазақ тілінде көмек көрсету."
    elif "ауа райы" in prompt:
        response = get_weather_in_almaty()
        update_user_dialog(f"Felix: {response}", 'assistant_message')
        get_yandex_voice_response(response)
        return
    elif "жасанды интеллект туралы не айтасыз" in prompt:
        response = "Жасанды интеллект — адамның интеллектуалдық функцияларын модельдеуге арналған технологиялар жиынтығы."
    elif "жаңалықтар" in prompt or "жаналықтар" in prompt:
        response = "Жаңалықтар беті 3 секундтан соң ашылады"
        update_user_dialog(f"Felix: {response}", 'assistant_message')
        get_yandex_voice_response(response)
        time.sleep(3)
        webbrowser.open("https://kaz.tengrinews.kz/")
        return
    elif "кино көрем" in prompt or "кино көргім келеді" in prompt:
        response = "Қандай жанрда көргіңіз келеді?"
        update_user_dialog(f"Felix: {response}", 'assistant_message')
        get_yandex_voice_response(response)
        genre_command = recognize_speech()
        update_user_dialog(f"Сіз (жанр): {genre_command}", 'user_message')
        if "қорқынышты" in genre_command or "хоррор" in genre_command:
            response = "Қорқынышты фильм тамашалап қайтыңыз"
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
            webbrowser.open("https://kinobar.my/uzhasyy/")
            return
        elif "фантастика" in genre_command:
            response = "Фантастикалық фильм тамашалап қайтыңыз"
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
            webbrowser.open("https://kinobar.my/fantastika/")
            return
        elif "білмеймін" in genre_command:
            response = "Онда сізді жай сайтқа жіберейін бе?"
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
            confirm = recognize_speech()
            if "ия" in confirm or "иә" in confirm:
                response = "Жақсы фильм тамашалап қайтыңыз"
                update_user_dialog(f"Felix: {response}", 'assistant_message')
                get_yandex_voice_response(response)
                webbrowser.open("https://kinobar.my/serialy/")
                return
            else:
                get_yandex_voice_response("Қайталаймын...")
        else:
            response = "Кешіріңіз, бұл жанрды таба алмадым."
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
    elif "мен туралы не айта аласың" in prompt:
        response = ("Сіздің атыңыздан оқыймын: Менің атым Арман, "
                    "мен Алматы мемлекеттік сервис және технология колледжінің үшінші курс студентімін, "
                    "менің басты мақсатым - жасанды интеллектті өз елімде барынша дамыту.")
    elif "әсет ағай" in prompt:
        response = "Әсет ағай практикадан сабақ берген. Қазіргі таңда, жаңа технологиялар мен программалау түрлерін зерттеуде."
    elif "зауре апай" in prompt:
        response = "Зауре Болатқызы қазіргі кездегі жас мамандарды дайындау, студенттерге программалау түрлерін үйрету сияқты істермен айналысады."
    elif "мақсат туралы ақпарат" in prompt:
        response = "Әскер Мақсат - менің тобымда оқитын жас маман. Оның ТАНК деген әдемі мопед атты тұлпары бар."
    # Проверка команд Яндекс и Spotify должна быть ДО проверки рецептов
    # Обработка составных команд типа "открой Яндекс и найди [запрос]"
    elif ("аш" in prompt.lower() or "ашы" in prompt.lower() or "открой" in prompt.lower() or "открыть" in prompt.lower()) and "яндекс" in prompt.lower():
        prompt_lower = prompt.lower()
        
        # Проверяем, есть ли вторая команда (разделители: "и", "және", "та", "да", "тап", "найди", "ізде", "косшы", "көру", "көрсет")
        separators = [" и ", " және ", " та ", " да ", " тап ", " найди ", " ізде ", " косшы ", " көру ", " көрсет ", " деген "]
        has_second_command = False
        search_query = ""
        
        # Сначала проверяем явные разделители
        for sep in separators:
            if sep in prompt_lower:
                parts = prompt_lower.split(sep, 1)
                if len(parts) > 1:
                    # Вторая часть - поисковый запрос
                    search_query = parts[1].strip()
                    has_second_command = True
                    break
        
            # Если нет явного разделителя, пытаемся извлечь запрос после слов "яндекс" и команд открытия
            if not has_second_command:
                # Ищем паттерны типа "яндексты ашта [запрос]" или "яндекс аш [запрос]"
                # Также обрабатываем "яндексты ашта [запрос] косшы" (косшы = көру = показать)
                patterns = [
                    r"яндексты?\s+аш[ты]?\s+(.+?)(?:\s+косшы|\s+көру|\s+көрсет|$)",
                    r"яндекс[ты]?\s+аш[ты]?\s+(.+?)(?:\s+косшы|\s+көру|\s+көрсет|$)",
                    r"аш[ты]?\s+яндекс[ты]?\s+(.+?)(?:\s+косшы|\s+көру|\s+көрсет|$)",
                    r"яндексты?\s+аш[ты]?\s+(.+)",
                    r"яндекс[ты]?\s+аш[ты]?\s+(.+)",
                    r"аш[ты]?\s+яндекс[ты]?\s+(.+)",
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, prompt_lower)
                    if match:
                        search_query = match.group(1).strip()
                        # Удаляем слова "косшы", "көру", "көрсет" из конца запроса если они есть
                        search_query = re.sub(r'\s+(косшы|көру|көрсет)$', '', search_query, flags=re.IGNORECASE)
                        if search_query:
                            has_second_command = True
                            break
        
        # Очищаем поисковый запрос от лишних слов
        if search_query:
            # Удаляем только служебные слова связанные с открытием и Яндексом
            # НЕ удаляем слова типа "кино", "фильм", "деген" так как они могут быть частью запроса
            cleanup_words = ["яндекс", "яндексты", "яндексте", "яндекс-те", "яндекс-де", "аш", "ашы", "открой", "открыть"]
            for word in cleanup_words:
                # Удаляем только если это отдельное слово
                search_query = re.sub(r'\b' + re.escape(word) + r'\b', '', search_query, flags=re.IGNORECASE)
            search_query = " ".join(search_query.split())
        
        # Открываем Яндекс
        webbrowser.open("https://yandex.kz/")
        response = "Яндекс ашылуда..."
        update_user_dialog(f"Felix: {response}", 'assistant_message')
        get_yandex_voice_response(response)
        
        # Если есть поисковый запрос, выполняем поиск
        if has_second_command and search_query:
            time.sleep(1)  # Небольшая задержка для открытия браузера
            search_yandex(search_query)
        elif not has_second_command:
            # Если нет второй команды, спрашиваем что искать
            response = "Яндекс-те не іздегіңіз келеді?"
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
            search_query = recognize_speech()
            if search_query:
                update_user_dialog(f"Сіз: {search_query}", 'user_message')
                search_yandex(search_query)
        return
    elif "найди" in prompt.lower() and "яндекс" in prompt.lower():
        # Команда типа "найди в яндексе [запрос]"
        query = prompt.lower()
        # Удаляем служебные слова
        for remove_word in ["найди", "в", "яндекс", "яндексте", "те", "де"]:
            query = query.replace(remove_word, " ").strip()
        # Убираем лишние пробелы
        query = " ".join(query.split())
        if query:
            search_yandex(query)
        else:
            # Если запрос не указан, спрашиваем у пользователя
            response = "Яндекс-те не іздегіңіз келеді?"
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
            search_query = recognize_speech()
            if search_query:
                update_user_dialog(f"Сіз: {search_query}", 'user_message')
                search_yandex(search_query)
            else:
                webbrowser.open("https://yandex.kz/")
                response = "Яндекс ашылуда..."
                update_user_dialog(f"Felix: {response}", 'assistant_message')
                get_yandex_voice_response(response)
        return
    elif "яндекс" in prompt.lower() and ("те" in prompt.lower() or "де" in prompt.lower() or "та" in prompt.lower()):
        # Обработка "яндекс те", "яндекс-те", "яндекс-де" и т.д.
        query = prompt.lower()
        # Заменяем "яндекс те" на "яндексте" для единообразной обработки
        query = query.replace("яндекс те", "яндексте").replace("яндекс-те", "яндексте").replace("яндекс-де", "яндексте")
        
        # Извлекаем запрос после ключевых слов
        for keyword in ["яндексте"]:
            if keyword in query:
                query = query.split(keyword, 1)[1].strip()
                break
        
        if query:
            search_yandex(query)
        else:
            # Если запрос не указан, открываем главную страницу Яндекса
            webbrowser.open("https://yandex.kz/")
            response = "Яндекс ашылуда..."
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
        return
    elif "включи" in prompt.lower() and ("спотифай" in prompt.lower() or "spotify" in prompt.lower() or "музыка" in prompt.lower()):
        # Команда типа "включи в спотифай [песня]"
        query = prompt.lower()
        # Удаляем служебные слова
        for remove_word in ["включи", "в", "спотифай", "spotify", "музыка", "та", "да"]:
            query = query.replace(remove_word, " ").strip()
        # Убираем лишние пробелы
        query = " ".join(query.split())
        if query:
            search_spotify(query)
        else:
            # Если запрос не указан, спрашиваем у пользователя
            response = "Қандай ән тапқыңыз келеді?"
            update_user_dialog(f"Felix: {response}", 'assistant_message')
            get_yandex_voice_response(response)
            song_query = recognize_speech()
            if song_query:
                update_user_dialog(f"Сіз: {song_query}", 'user_message')
                search_spotify(song_query)
            else:
                launch_spotify()
        return
    elif "спотифайда" in prompt.lower() or "spotify-та" in prompt.lower() or "spotify-да" in prompt.lower():
        # Извлекаем запрос после ключевых слов
        query = prompt.lower()
        for keyword in ["спотифайда", "spotify-та", "spotify-да"]:
            if keyword in query:
                query = query.split(keyword, 1)[1].strip()
                break
        if query:
            search_spotify(query)
        else:
            # Если запрос не указан, просто открываем Spotify
            launch_spotify()
        return
    elif "спотифай" in prompt.lower() or "spotify" in prompt.lower() or "музыка" in prompt.lower():
        # Проверяем, есть ли запрос после ключевого слова
        query_parts = prompt.lower().split()
        spotify_index = -1
        for i, word in enumerate(query_parts):
            if "спотифай" in word or "spotify" in word or "музыка" in word:
                spotify_index = i
                break
        
        if spotify_index >= 0 and spotify_index < len(query_parts) - 1:
            # Есть запрос после ключевого слова
            query = " ".join(query_parts[spotify_index + 1:])
            search_spotify(query)
        else:
            # Просто открываем Spotify
            launch_spotify()
        return
    elif "стим" in prompt.lower() or "steam" in prompt.lower() or "ойын" in prompt.lower():
        launch_steam()
        return
    elif "хром" in prompt.lower() or "chrome" in prompt.lower() or "браузер" in prompt.lower():
        launch_chrome()
        return
    elif "ютуб" in prompt.lower() or "youtube" in prompt.lower():
        launch_youtube()
        return
    elif "сұрақ жоқ" in prompt or "жоқ" in prompt or "сау бол" in prompt or "тоқта" in prompt:
        response = "Мені қолданғаныңызға рахмет, көмек қолын созуға әрдайым дайынмын. Сіздермен бірге болған Felix. Көріскенше, сау болыңыз."
    elif "пайдалы қазақша сөз тіркестері" in prompt or "қазақша фразалар" in prompt or "сөз тіркестері" in prompt:
        response = "Мына пайдалы қазақша сөз тіркестерін қараңыз:"
        for phrase in kazakh_phrases:
            response += "\n" + phrase
        user_dialog.insert(tk.END, f"Felix: {response}\n")
        get_yandex_voice_response("Мына пайдалы қазақша сөз тіркестерін қараңыз.")
        return
    elif "рецепт" in prompt or "қазақша тағамдар" in prompt or "рецепттер" in prompt or "ас мәзірі" in prompt:
        response = "Қандай тағамның рецептін білгіңіз келеді?"
        user_dialog.insert(tk.END, f"Felix: {response}\n")
        get_yandex_voice_response(response)
        dish_command = recognize_speech()
        user_dialog.insert(tk.END, f"Сіз (тағам): {dish_command}\n")
        dish = dish_command.lower()
        if dish in recipes:
            response = recipes[dish]
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        else:
            response = "Кешіріңіз, мен ол тағамның рецептін білмеймін."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
    elif "қазақстанның картасы" in prompt or "карта" in prompt or "қазақстанның картасын көрсет" in prompt:
        response = "Қазақстанның картасы ашылады."
        user_dialog.insert(tk.END, f"Felix: {response}\n")
        get_yandex_voice_response(response)
        webbrowser.open("https://www.google.com/maps/place/Kazakhstan/")
        return
    elif "ұлттық батырлар" in prompt or "тарихи оқиғалар" in prompt or "батырлар" in prompt or "тарих" in prompt:
        response = "Қай батыр немесе тарихи оқиға туралы білгіңіз келеді?"
        user_dialog.insert(tk.END, f"Felix: {response}\n")
        get_yandex_voice_response(response)
        hero_command = recognize_speech()
        user_dialog.insert(tk.END, f"Сіз (батыр/оқиға): {hero_command}\n")
        hero = hero_command.lower()
        if hero in heroes:
            response = heroes[hero]
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        else:
            response = "Кешіріңіз, мен ол туралы ақпарат білмеймін."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
    elif "мейрамдар" in prompt or "напоминание" in prompt or "ескерту" in prompt:
        response = "Қазақстанның маңызды мейрамдары:"
        for holiday in holidays:
            response += "\n" + holiday
        user_dialog.insert(tk.END, f"Felix: {response}\n")
        get_yandex_voice_response("Қазақстанның маңызды мейрамдарын қараңыз.")
        return
    elif "түрлендір" in prompt or "айналдыр" in prompt or "есепте" in prompt:
        response = "Қандай есептеуді немесе түрлендіруді орындау керек екенін айтыңыз."
        user_dialog.insert(tk.END, f"Felix: {response}\n")
        get_yandex_voice_response(response)
        calc_command = recognize_speech()
        user_dialog.insert(tk.END, f"Сіз (есептеу): {calc_command}\n")
        if "теңге" in calc_command and "долларға" in calc_command:
            amount = extract_number(calc_command)
            if amount:
                rate = 0.0023
                converted = amount * rate
                response = f"{amount} теңге {converted:.2f} долларға тең"
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
            else:
                response = "Соманы анықтай алмадым."
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
        elif "километр" in calc_command and "мильге" in calc_command:
            amount = extract_number(calc_command)
            if amount:
                converted = amount * 0.621371
                response = f"{amount} километр {converted:.2f} мильге тең"
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
            else:
                response = "Соманы анықтай алмадым."
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
        else:
            response = "Кешіріңіз, бұл есептеуді орындай алмадым."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
    else:
        # Используем Gemini для ответа на неизвестные вопросы
        response = get_gemini_response(prompt)
        update_user_dialog(f"Felix: {response}", 'assistant_message')
        get_yandex_voice_response(response)
        return

    update_user_dialog(f"Felix: {response}", 'assistant_message')
    get_yandex_voice_response(response)

def process_request_with_text(text):
    text_input.delete(0, 'end')
    text_input.insert(0, text)
    process_request()

def process_voice_command(command):
    """Обрабатывает голосовую команду после активации"""
    global assistant_active
    
    if not command:
        return
    
    # Обрабатываем команду так же, как текстовый ввод
    command_lower = command.lower().strip()
    
    # Обрабатываем через обычную функцию process_request
    # Создаем временный текст в поле ввода
    original_text = text_input.get()
    placeholder_text = "Сұрағыңызды енгізіңіз..."
    
    # Сохраняем оригинальный цвет
    original_fg = text_input.cget("fg")
    
    text_input.delete(0, 'end')
    text_input.insert(0, command)
    text_input.config(fg="#FFFFFF")  # Устанавливаем нормальный цвет для команды
    
    # Обрабатываем команду
    process_request()
    
    # Восстанавливаем placeholder если нужно
    if not original_text or original_text == placeholder_text:
        text_input.delete(0, 'end')
        text_input.insert(0, placeholder_text)
        text_input.config(fg="#6B6B7B")
    else:
        text_input.delete(0, 'end')
        text_input.insert(0, original_text)
        text_input.config(fg=original_fg)

def main():
    global assistant_active
    while assistant_active:
        get_yandex_voice_response("Егер сізде сұрақ болса, маған айтуыңызды өтінемін.")
        if not assistant_active:
            break
        command = recognize_speech()
        if not assistant_active or not command:
            break

        if "атыңыз кім" in command or "как тебя зовут" in command:
            response = "Мен Felix. Менің басты жұмысым қолданушыға ыңғайлы және қазақ тілінде көмек көрсету."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        elif "ауа райы" in command:
            response = get_weather_in_almaty()
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        elif "Ақжол ағайды туған күнімен құттыұтау" in command:
            response = "Ақжол братан на аве, ЕНТ 50-50 в кармане. Ақжол ағай, сізді келіп жатқан туған күніңізбен құттықтаймыз. Әрқашан күлімдеп, біздің және болашақтағы барлық студенттеріңіздің грантқа түсуін қуанышпен қарсы алғаныңызды қалаймыз!!!"
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        elif "жасанды интеллект туралы не айтасыз" in command:
            response = "Жасанды интеллект — адамның интеллектуалдық функцияларын модельдеуге арналған технологиялар жиынтығы."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        elif "жаңалықтар" in command or "жаналықтар" in command:
            response = "Жаңалықтар беті 3 секундтан соң ашылады"
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
            time.sleep(3)
            webbrowser.open("https://kaz.tengrinews.kz/")
            break
        elif "жобаның жүзеге асу процесі" in command or "жоба туралы ақпарат" in command:
            response = (
                "Құрметті ұстаздар, құрметті қонақтар және достар!\n"
                "Бүгін сіздерге өзімнің қазақ тіліндегі жасанды интеллект негізіндегі ассистентімді таныстырғым келеді. "
                "Бұл жоба менің көп уақытымды, күш-жігерімді және шығармашылығымды талап етті. Сонымен қатар, бұл жобаның іске асуына "
                "үлкен қолдау көрсеткен адамдарға да алғысым шексіз.\n\n"
                "Жасанды интеллект және оның Қазақстандағы дамуы\n"
                "Жасанды интеллект — бұл қазіргі заманның ең маңызды технологияларының бірі. Ол адамның ойлау қабілетін компьютерлік жүйелер арқылы жүзеге асыруға мүмкіндік береді. "
                "Әлемде жасанды интеллект медицинада, білім беруде, өнеркәсіпте кеңінен қолданылады. Бірақ Қазақстанда, әсіресе қазақ тілінде, бұл сала әлі де болса дамуды қажет етеді.\n"
                "Менің басты мақсатым — қазақ тілінде жұмыс істейтін ассистент жасап, елімізде жасанды интеллекттің дамуына үлес қосу. "
                "Қазақ тілі — біздің мәдениетіміздің, руханиятымыздың негізі. Сондықтан да, технологиялық әлемде оның орны ерекше болуы тиіс.\n\n"
                "Жобаның жүзеге асу процесі\n\n"
                "Жобаны іске асыру барысында мен бірнеше кезеңнен өттім:\n"
                "1. Идеяны қалыптастыру: Ассистентті жасау идеясы менің көкейімде ұзақ уақыт бойы жүрді. Бұл идеяны дамытып, нақты мақсаттар қоюға көмектескен — менің ұстаздарым мен интернет парақшалар. "
                "Олар өздерінің білімімен, тәжірибесімен бөлісіп, маған бағыт-бағдар берді. Сонымен қатар, түрлі ақпараттар мен жасанды интелекттің мүмкіндіктерімен танысып шығу арқылы идея ала алдым.\n"
                "2. Жоспарлау және зерттеу: Жасанды интеллекттің жұмыс принциптерін, дауысты тану және синтездеу технологияларын зерттедім. Сіздердің кеңестеріңіз бен қолдауларыңыз осы кезеңде ерекше маңызды болды.\n"
                "3. Дамыту кезеңі:\n"
                "   o Бағдарламалау тілі: Python тілін таңдадым, себебі ол жасанды интеллект пен деректерді өңдеуге өте қолайлы.\n"
                "   o Дауысты тану: Vosk кітапханасының қазақ тіліндегі моделін қолдандым. Бұл модель офлайн режимде жұмыс істеп, жоғары дәлдікпен дауысты тануға мүмкіндік береді.\n"
                "   o Дауысты синтездеу: Яндекс ТТС API арқылы ассистенттің қазақ тілінде сөйлеуін қамтамасыз еттім. Бұл технология табиғи дыбыстауды қамтамасыз етеді.\n"
                "   o Графикалық интерфейс: Tkinter кітапханасының көмегімен қолданушыға ыңғайлы интерфейс жасалды. Бұл бөлімде интерфейстің дизайны мен функционалдығына ерекше назар аударылды.\n"
                "4. Тестілеу және жетілдіру: Ассистенттің жұмысын бірнеше рет сынақтан өткізіп, қателіктерін түзеттім. Бұл кезеңде сіздердің пікірлеріңіз бен ұсыныстарыңыз өте құнды болды.\n"
                "5. Қосымша функциялар қосу: Ассистенттің мүмкіндіктерін кеңейту үшін жаңа функциялар қостым. Мұнда да менің ұстаздарымның идеялары мен кеңестері үлкен рөл атқарды.\n\n"
                "Ассистенттің функциялары\n"
                "• Дауысты тану және жауап беру: Қолданушының қазақ тіліндегі сөйлеуін таниды және сәйкесінше жауап береді.\n"
                "• Ауа райы туралы ақпарат: Алматы қаласының ағымдағы ауа райын хабарлайды.\n"
                "• Жаңалықтармен бөлісу: Соңғы жаңалықтарды айтып, сәйкес веб-сайттарға бағыттайды.\n"
                "• Қазақ тілін үйренуге көмек: Пайдалы сөз тіркестері мен фразаларды ұсынады.\n"
                "• Ұлттық тағамдардың рецепттері: Қазақтың ұлттық тағамдарының рецепттерін айтып, мәдениетімізді насихаттайды.\n"
                "• Тарихи ақпарат: Ұлттық батырлар мен тарихи тұлғалар туралы мәлімет береді.\n"
                "• Есептеулер және түрлендірулер: Қарапайым математикалық есептерді шығарып, валюталарды және өлшем бірліктерін түрлендіреді.\n\n"
                "Жобаның мәні және болашағы\n"
                "Бұл ассистент — қазақ тіліндегі технологиялық дамудың бір қадамы ғана. Оның көмегімен қазақ тілінде сөйлейтін адамдарға ыңғайлы, түсінікті және пайдалы құрал ұсынамыз. Жобаның болашағы зор деп ойлаймын, себебі ол тек бастамасы ғана.\n\n"
                "Алғыс сөз\n"
                "Осы жобаны жүзеге асыру барысында маған қолдау көрсеткен барлық адамдарға шын жүректен алғысымды білдіремін. Әсіресе, Әсет ағай мен Зауре Болатқызына — сіздердің білімдеріңіз бен тәжірибелеріңіз мен үшін өте маңызды болды. Сондай-ақ, сіздерге, құрметті қауым, шабыт бергендеріңіз үшін рақмет айтамын.\n\n"
                "Қорытынды\n"
                "Біз бірге қазақ тілінің технологиялық кеңістікте дамуына үлес қосып жатырмыз. Жасанды интеллектті қазақ тілінде дамыту — бұл біздің мәдениетімізді, тілімізді сақтап, оны жаңа деңгейге көтеру деген сөз. Алдағы уақытта да осы бағытта жұмыс істеп, жобаны жетілдіруге ниеттімін.\n"
                "Назарларыңызға көп рақмет!"
            )
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        elif "кино көрем" in command or "кино көргім келеді" in command:
            response = "Қандай жанрда көргіңіз келеді?"
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
            genre_command = recognize_speech()
            user_dialog.insert(tk.END, f"Сіз (жанр): {genre_command}\n")
            if "қорқынышты" in genre_command or "хоррор" in genre_command:
                response = "Қорқынышты фильм тамашалап қайтыңыз"
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
                webbrowser.open("https://kinobar.my/uzhasyy/")
                break
            elif "фантастика" in genre_command:
                response = "Фантастикалық фильм тамашалап қайтыңыз"
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
                webbrowser.open("https://kinobar.my/fantastika/")
                break
            elif "білмеймін" in genre_command:
                response = "Онда сізді жай сайтқа жіберейін бе?"
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
                confirm = recognize_speech()
                if "ия" in confirm or "иә" in confirm:
                    response = "Жақсы фильм тамашалап қайтыңыз"
                    user_dialog.insert(tk.END, f"Felix: {response}\n")
                    get_yandex_voice_response(response)
                    webbrowser.open("https://kinobar.my/serialy/")
                    break
                else:
                    get_yandex_voice_response("Қайталаймын...")
            else:
                response = "Кешіріңіз, бұл жанрды таба алмадым."
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
        elif "мен туралы не айта аласың" in command:
            response = ("Сіздің атыңыздан оқыймын: Менің атым Мықтыбай Нұрдәулет Берікұлы, "
                        "мен Алт универінің 1 курс студентімін, "
                        "менің басты мақсатым - жасанды интеллектті өз елімде барынша дамыту.")
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        elif "әсет ағай" in command:
            response = "Әсет ағай практикадан сабақ берген. Қазіргі таңда, жаңа технологиялар мен программалау түрлерін зерттеуде."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        elif "зауре апай" in command:
            response = "Зауре Болатқызы қазіргі кездегі жас мамандарды дайындау, студенттерге программалау түрлерін үйрету сияқты істермен айналысады."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        elif "мақсат туралы ақпарат" in command:
            response = "Әскер Мақсат - менің тобымда оқитын жас маман. Оның ТАНК деген әдемі мопед атты тұлпары бар."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
        elif "сәлем" in command:
            respond_to_hello()
        # Проверка команд Яндекс и Spotify должна быть ДО проверки рецептов
        # Обработка составных команд типа "открой Яндекс и найди [запрос]"
        elif ("аш" in command.lower() or "ашы" in command.lower() or "открой" in command.lower() or "открыть" in command.lower()) and "яндекс" in command.lower():
            command_lower = command.lower()
            
            # Проверяем, есть ли вторая команда (разделители: "и", "және", "та", "да", "тап", "найди", "ізде", "косшы", "көру", "көрсет")
            separators = [" и ", " және ", " та ", " да ", " тап ", " найди ", " ізде ", " косшы ", " көру ", " көрсет ", " деген "]
            has_second_command = False
            search_query = ""
            
            # Сначала проверяем явные разделители
            for sep in separators:
                if sep in command_lower:
                    parts = command_lower.split(sep, 1)
                    if len(parts) > 1:
                        # Вторая часть - поисковый запрос
                        search_query = parts[1].strip()
                        has_second_command = True
                        break
            
            # Если нет явного разделителя, пытаемся извлечь запрос после слов "яндекс" и команд открытия
            if not has_second_command:
                # Ищем паттерны типа "яндексты ашта [запрос]" или "яндекс аш [запрос]"
                # Также обрабатываем "яндексты ашта [запрос] косшы" (косшы = көру = показать)
                patterns = [
                    r"яндексты?\s+аш[ты]?\s+(.+?)(?:\s+косшы|\s+көру|\s+көрсет|$)",
                    r"яндекс[ты]?\s+аш[ты]?\s+(.+?)(?:\s+косшы|\s+көру|\s+көрсет|$)",
                    r"аш[ты]?\s+яндекс[ты]?\s+(.+?)(?:\s+косшы|\s+көру|\s+көрсет|$)",
                    r"яндексты?\s+аш[ты]?\s+(.+)",
                    r"яндекс[ты]?\s+аш[ты]?\s+(.+)",
                    r"аш[ты]?\s+яндекс[ты]?\s+(.+)",
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, command_lower)
                    if match:
                        search_query = match.group(1).strip()
                        # Удаляем слова "косшы", "көру", "көрсет" из конца запроса если они есть
                        search_query = re.sub(r'\s+(косшы|көру|көрсет)$', '', search_query, flags=re.IGNORECASE)
                        if search_query:
                            has_second_command = True
                            break
            
            # Очищаем поисковый запрос от лишних слов
            if search_query:
                # Удаляем только служебные слова связанные с открытием и Яндексом
                # НЕ удаляем слова типа "кино", "фильм", "деген" так как они могут быть частью запроса
                cleanup_words = ["яндекс", "яндексты", "яндексте", "яндекс-те", "яндекс-де", "аш", "ашы", "открой", "открыть"]
                for word in cleanup_words:
                    # Удаляем только если это отдельное слово
                    search_query = re.sub(r'\b' + re.escape(word) + r'\b', '', search_query, flags=re.IGNORECASE)
                search_query = " ".join(search_query.split())
            
            # Открываем Яндекс
            webbrowser.open("https://yandex.kz/")
            response = "Яндекс ашылуда..."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
            
            # Если есть поисковый запрос, выполняем поиск
            if has_second_command and search_query:
                time.sleep(1)  # Небольшая задержка для открытия браузера
                search_yandex(search_query)
            elif not has_second_command:
                # Если нет второй команды, спрашиваем что искать
                response = "Яндекс-те не іздегіңіз келеді?"
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
                search_query = recognize_speech()
                if search_query:
                    user_dialog.insert(tk.END, f"Сіз: {search_query}\n")
                    search_yandex(search_query)
        elif "найди" in command.lower() and "яндекс" in command.lower():
            # Команда типа "найди в яндексе [запрос]"
            query = command.lower()
            # Удаляем служебные слова
            for remove_word in ["найди", "в", "яндекс", "яндексте", "те", "де"]:
                query = query.replace(remove_word, " ").strip()
            # Убираем лишние пробелы
            query = " ".join(query.split())
            if query:
                search_yandex(query)
            else:
                # Если запрос не указан, спрашиваем у пользователя
                response = "Яндекс-те не іздегіңіз келеді?"
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
                search_query = recognize_speech()
                if search_query:
                    user_dialog.insert(tk.END, f"Сіз: {search_query}\n")
                    search_yandex(search_query)
                else:
                    webbrowser.open("https://yandex.kz/")
                    response = "Яндекс ашылуда..."
                    user_dialog.insert(tk.END, f"Felix: {response}\n")
                    get_yandex_voice_response(response)
        elif "яндекс" in command.lower() and ("те" in command.lower() or "де" in command.lower() or "та" in command.lower()):
            # Обработка "яндекс те", "яндекс-те", "яндекс-де" и т.д.
            query = command.lower()
            # Заменяем "яндекс те" на "яндексте" для единообразной обработки
            query = query.replace("яндекс те", "яндексте").replace("яндекс-те", "яндексте").replace("яндекс-де", "яндексте")
            
            # Извлекаем запрос после ключевых слов
            for keyword in ["яндексте"]:
                if keyword in query:
                    query = query.split(keyword, 1)[1].strip()
                    break
            
            if query:
                search_yandex(query)
            else:
                webbrowser.open("https://yandex.kz/")
                response = "Яндекс ашылуда..."
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
        elif "включи" in command.lower() and ("спотифай" in command.lower() or "spotify" in command.lower() or "музыка" in command.lower()):
            # Команда типа "включи в спотифай [песня]"
            query = command.lower()
            # Удаляем служебные слова
            for remove_word in ["включи", "в", "спотифай", "spotify", "музыка", "та", "да"]:
                query = query.replace(remove_word, " ").strip()
            # Убираем лишние пробелы
            query = " ".join(query.split())
            if query:
                search_spotify(query)
            else:
                # Если запрос не указан, спрашиваем у пользователя
                response = "Қандай ән тапқыңыз келеді?"
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
                song_query = recognize_speech()
                if song_query:
                    user_dialog.insert(tk.END, f"Сіз: {song_query}\n")
                    search_spotify(song_query)
                else:
                    launch_spotify()
        elif "спотифайда" in command.lower() or "spotify-та" in command.lower() or "spotify-да" in command.lower():
            # Извлекаем запрос после ключевых слов
            query = command.lower()
            for keyword in ["спотифайда", "spotify-та", "spotify-да"]:
                if keyword in query:
                    query = query.split(keyword, 1)[1].strip()
                    break
            if query:
                search_spotify(query)
            else:
                launch_spotify()
        elif "спотифай" in command.lower() or "spotify" in command.lower() or "музыка" in command.lower():
            # Проверяем, есть ли запрос после ключевого слова
            query_parts = command.lower().split()
            spotify_index = -1
            for i, word in enumerate(query_parts):
                if "спотифай" in word or "spotify" in word or "музыка" in word:
                    spotify_index = i
                    break
            
            if spotify_index >= 0 and spotify_index < len(query_parts) - 1:
                # Есть запрос после ключевого слова
                query = " ".join(query_parts[spotify_index + 1:])
                search_spotify(query)
            else:
                launch_spotify()
        elif "найди" in command.lower() and "яндекс" in command.lower():
            # Команда типа "найди в яндексе [запрос]"
            query = command.lower()
            # Удаляем служебные слова
            for remove_word in ["найди", "в", "яндекс", "яндексте", "те", "де"]:
                query = query.replace(remove_word, " ").strip()
            # Убираем лишние пробелы
            query = " ".join(query.split())
            if query:
                search_yandex(query)
            else:
                # Если запрос не указан, спрашиваем у пользователя
                response = "Яндекс-те не іздегіңіз келеді?"
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
                search_query = recognize_speech()
                if search_query:
                    user_dialog.insert(tk.END, f"Сіз: {search_query}\n")
                    search_yandex(search_query)
                else:
                    webbrowser.open("https://yandex.kz/")
                    response = "Яндекс ашылуда..."
                    user_dialog.insert(tk.END, f"Felix: {response}\n")
                    get_yandex_voice_response(response)
        elif "стим" in command.lower() or "steam" in command.lower() or "ойын" in command.lower():
            launch_steam()
        elif "хром" in command.lower() or "chrome" in command.lower() or "браузер" in command.lower():
            launch_chrome()
        elif "ютуб" in command.lower() or "youtube" in command.lower():
            launch_youtube()
        elif "сұрақ жоқ" in command or "жоқ" in command or "сау бол" in command or "тоқта" in command:
            response = "Мені қолданғаныңызға рахмет, көмек қолын созуға әрдайым дайынмын. Сіздермен бірге болған Felix. Көріскенше, сау болыңыз."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
            break
        elif "пайдалы қазақша сөз тіркестері" in command or "қазақша фразалар" in command or "сөз тіркестері" in command:
            response = "Мына пайдалы қазақша сөз тіркестерін қараңыз:"
            for phrase in kazakh_phrases:
                response += "\n" + phrase
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response("Мына пайдалы қазақша сөз тіркестерін қараңыз.")
        elif "рецепт" in command or "қазақша тағамдар" in command or "рецепттер" in command or "ас мәзірі" in command:
            response = "Қандай тағамның рецептін білгіңіз келеді?"
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
            dish_command = recognize_speech()
            user_dialog.insert(tk.END, f"Сіз (тағам): {dish_command}\n")
            dish = dish_command.lower()
            if dish in recipes:
                response = recipes[dish]
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
            else:
                response = "Кешіріңіз, мен ол тағамның рецептін білмеймін."
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
        elif "қазақстанның картасы" in command or "карта" in command or "қазақстанның картасын көрсет" in command:
            response = "Қазақстанның картасы ашылады."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
            webbrowser.open("https://www.google.com/maps/place/Kazakhstan/")
            break
        elif "ұлттық батырлар" in command or "тарихи оқиғалар" in command or "батырлар" in command or "тарих" in command:
            response = "Қай батыр немесе тарихи оқиға туралы білгіңіз келеді?"
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
            hero_command = recognize_speech()
            user_dialog.insert(tk.END, f"Сіз (батыр/оқиға): {hero_command}\n")
            hero = hero_command.lower()
            if hero in heroes:
                response = heroes[hero]
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
            else:
                response = "Кешіріңіз, мен ол туралы ақпарат білмеймін."
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
        elif "мейрамдар" in command or "напоминание" in command or "ескерту" in command:
            response = "Қазақстанның маңызды мейрамдары:"
            for holiday in holidays:
                response += "\n" + holiday
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response("Қазақстанның маңызды мейрамдарын қараңыз.")
        elif "түрлендір" in command or "айналдыр" in command or "есепте" in command:
            response = "Қандай есептеуді немесе түрлендіруді орындау керек екенін айтыңыз."
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
            calc_command = recognize_speech()
            user_dialog.insert(tk.END, f"Сіз (есептеу): {calc_command}\n")
            if "теңге" in calc_command and "долларға" in calc_command:
                amount = extract_number(calc_command)
                if amount:
                    rate = 0.0023
                    converted = amount * rate
                    response = f"{amount} теңге {converted:.2f} долларға тең"
                    user_dialog.insert(tk.END, f"Felix: {response}\n")
                    get_yandex_voice_response(response)
                else:
                    response = "Соманы анықтай алмадым."
                    user_dialog.insert(tk.END, f"Felix: {response}\n")
                    get_yandex_voice_response(response)
            elif "километр" in calc_command and "мильге" in calc_command:
                amount = extract_number(calc_command)
                if amount:
                    converted = amount * 0.621371
                    response = f"{amount} километр {converted:.2f} мильге тең"
                    user_dialog.insert(tk.END, f"Felix: {response}\n")
                    get_yandex_voice_response(response)
                else:
                    response = "Соманы анықтай алмадым."
                    user_dialog.insert(tk.END, f"Felix: {response}\n")
                    get_yandex_voice_response(response)
            else:
                response = "Кешіріңіз, бұл есептеуді орындай алмадым."
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
        else:
            response = "Кешіріңіз, мен бұл сұрақты түсінбедім. Оны Жасанды Интелекте іздейін бе?"
            user_dialog.insert(tk.END, f"Felix: {response}\n")
            get_yandex_voice_response(response)
            confirm = recognize_speech()
            if "ия" in confirm or "иә" in confirm:
                response = "Іздеу жүйесі ашылады."
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
                open_free_chatgpt()
                break
            else:
                response = "Сұрағыңызға жауап бере алмадым."
                user_dialog.insert(tk.END, f"Felix: {response}\n")
                get_yandex_voice_response(response)
    window.after(0, update_user_dialog, "Felix жұмысын тоқтатты.", 'assistant_message')


def start_or_stop_assistant():
    global assistant_active, assistant_thread, mic_button

    if assistant_active:
        assistant_active = False
        if mic_button:
            mic_button.config(bg="#E74C3C", activebackground="#C0392B")
        update_user_dialog("Felix: Микрофон өшірілді.", 'assistant_message')
        window.after(0, stop_gif_animation)
    else:
        assistant_active = True
        if mic_button:
            mic_button.config(bg="#27AE60", activebackground="#229954")
        update_user_dialog("Felix: Микрофон қосылды. 🎤", 'assistant_message')
        assistant_thread = threading.Thread(target=main)
        assistant_thread.start()

def respond_to_hello():
    response = "Сәлем достым, мен Felix - қазақ тіліндегі AI көмекші."
    update_user_dialog(f"Felix: {response}", 'assistant_message')
    get_yandex_voice_response(response)

def set_voice_madi():
    global selected_voice
    selected_voice = "madi"
    voice_label.config(text="Қазіргі версия: Мади")

def set_voice_amira():
    global selected_voice
    selected_voice = "amira"
    voice_label.config(text="Қазіргі версия: Амира")
def create_rounded_button(parent, text, command, bg_color="#4A90E2", hover_color="#357ABD", width=120, height=40):
    """Создает красивую кнопку со скругленными углами и hover эффектом"""
    btn_frame = tk.Frame(parent, bg=parent.cget("bg"), width=width, height=height)
    btn_frame.pack_propagate(False)
    
    btn = tk.Button(btn_frame, text=text, command=command, 
                   bg=bg_color, fg="white", font=("Segoe UI", 10, "bold"),
                   relief="flat", bd=0, cursor="hand2",
                   activebackground=hover_color, activeforeground="white",
                   padx=15, pady=8)
    btn.pack(fill="both", expand=True)
    
    def on_enter(e):
        btn.config(bg=hover_color)
    
    def on_leave(e):
        btn.config(bg=bg_color)
    
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    
    return btn_frame

def create_icon_button(parent, text, command, bg_color="#2C3E50", hover_color="#34495E", size=42):
    """Создает круглую кнопку с иконкой"""
    btn = tk.Button(parent, text=text, command=command,
                   bg=bg_color, fg="white", font=("Segoe UI", 14),
                   relief="flat", bd=0, cursor="hand2",
                   width=2, height=1,
                   activebackground=hover_color, activeforeground="white",
                   padx=8, pady=8)
    
    def on_enter(e):
        btn.config(bg=hover_color)
    
    def on_leave(e):
        btn.config(bg=bg_color)
    
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    
    return btn

def create_interface():
    global text_input, user_dialog, voice_label, gif_label, gif_frames, gif_index, gif_animation_running, window, mic_button
    
    window = tk.Tk()
    window.title("Felix - Қазақ тіліндегі AI көмекші")
    window.geometry("700x850")
    window.configure(bg="#0F0F1E")
    window.resizable(True, True)
    
    # Минимальный размер окна
    window.minsize(600, 700)
    
    # Современная цветовая схема
    bg_dark = "#0F0F1E"
    bg_medium = "#1A1A2E"
    bg_light = "#16213E"
    bg_input = "#0E1621"
    accent_blue = "#5B8DEF"
    accent_hover = "#4A7DD9"
    accent_purple = "#9B59B6"
    accent_green = "#2ECC71"
    accent_orange = "#F39C12"
    text_primary = "#FFFFFF"
    text_secondary = "#A0A0B0"
    text_muted = "#6B6B7B"
    user_msg_bg = "#5B8DEF"
    assistant_msg_bg = "#1A1A2E"
    border_color = "#2A2A3E"
    
    # Верхняя панель с заголовком (градиентный эффект)
    header_frame = tk.Frame(window, bg=bg_medium, height=100)
    header_frame.pack(fill="x", padx=0, pady=0)
    header_frame.pack_propagate(False)
    
    # Внутренний фрейм для отступов
    header_inner = tk.Frame(header_frame, bg=bg_medium)
    header_inner.pack(fill="both", expand=True, padx=20, pady=15)
    
    title_label = tk.Label(header_inner, 
                          text="✨ Felix", 
                          font=("Segoe UI", 24, "bold"), 
                          fg=text_primary, 
                          bg=bg_medium)
    title_label.pack(anchor="w", pady=(0, 5))
    
    subtitle_label = tk.Label(header_inner, 
                            text="Сізге қандай көмек қажет?", 
                            font=("Segoe UI", 12), 
                            fg=text_secondary, 
                            bg=bg_medium)
    subtitle_label.pack(anchor="w")
    
    # Выбор голоса (улучшенный дизайн)
    voice_frame = tk.Frame(window, bg=bg_dark)
    voice_frame.pack(pady=(15, 10), padx=20, fill="x")
    
    voice_container = tk.Frame(voice_frame, bg=bg_medium, relief="flat", bd=1, highlightbackground=border_color, highlightthickness=1)
    voice_container.pack(fill="x", padx=0, pady=0)
    
    voice_inner = tk.Frame(voice_container, bg=bg_medium)
    voice_inner.pack(fill="x", padx=12, pady=8)
    
    voice_label_text = tk.Label(voice_inner, 
                               text="🎙️ Дауыс:", 
                               font=("Segoe UI", 10), 
                               fg=text_secondary, 
                               bg=bg_medium)
    voice_label_text.pack(side="left", padx=(0, 10))
    
    voice_menu = tk.Menubutton(voice_inner, 
                              text="Мади ▼", 
                              font=("Segoe UI", 11, "bold"), 
                              fg=accent_blue, 
                              bg=bg_light, 
                              relief="flat",
                              cursor="hand2",
                              activebackground=accent_blue,
                              activeforeground="white",
                              padx=12, pady=5)
    voice_menu.menu = tk.Menu(voice_menu, tearoff=0, bg=bg_medium, fg=text_primary,
                             activebackground=accent_blue, activeforeground=text_primary,
                             font=("Segoe UI", 10), bd=0)
    voice_menu["menu"] = voice_menu.menu
    
    voice_menu.menu.add_command(label="Мади", command=lambda: (set_voice_madi(), voice_menu.config(text="Мади ▼")))
    voice_menu.menu.add_command(label="Амира", command=lambda: (set_voice_amira(), voice_menu.config(text="Амира ▼")))
    voice_menu.pack(side="left")
    
    voice_label = tk.Label(voice_inner, 
                          text="", 
                          font=("Segoe UI", 9), 
                          fg=text_muted, 
                          bg=bg_medium)
    voice_label.pack(side="left", padx=(15, 0))
    
    # Область диалога с прокруткой (улучшенный дизайн)
    dialog_container = tk.Frame(window, bg=bg_dark)
    dialog_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
    
    dialog_frame = tk.Frame(dialog_container, bg=bg_medium, relief="flat", bd=1, highlightbackground=border_color, highlightthickness=1)
    dialog_frame.pack(fill="both", expand=True)
    
    scrollbar = tk.Scrollbar(dialog_frame, bg=bg_medium, troughcolor=bg_medium, 
                            activebackground=accent_blue, width=10, bd=0)
    scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2)
    
    user_dialog = tk.Text(dialog_frame, 
                         wrap="word", 
                         bg=bg_medium, 
                         font=("Segoe UI", 12), 
                         height=20, 
                         bd=0, 
                         padx=20, 
                         pady=20, 
                         fg=text_primary,
                         insertbackground=accent_blue,
                         yscrollcommand=scrollbar.set,
                         relief="flat",
                         selectbackground=accent_blue,
                         selectforeground="white")
    user_dialog.pack(fill="both", expand=True)
    scrollbar.config(command=user_dialog.yview)
    
    # Настройка тегов для сообщений (улучшенный дизайн)
    user_dialog.tag_configure("user_message", 
                             justify="right", 
                             background=user_msg_bg, 
                             foreground=text_primary, 
                             lmargin1=80, 
                             lmargin2=80, 
                             rmargin=20,
                             spacing1=8,
                             spacing2=3,
                             spacing3=8,
                             relief="flat",
                             borderwidth=0,
                             font=("Segoe UI", 11))
    
    user_dialog.tag_configure("assistant_message", 
                             justify="left", 
                             background=assistant_msg_bg, 
                             foreground=text_primary, 
                             lmargin1=20, 
                             lmargin2=20, 
                             rmargin=80,
                             spacing1=8,
                             spacing2=3,
                             spacing3=8,
                             relief="flat",
                             borderwidth=0,
                             font=("Segoe UI", 11))
    
    # Поле ввода с кнопками (улучшенный дизайн)
    input_container = tk.Frame(window, bg=bg_dark)
    input_container.pack(fill="x", padx=20, pady=(0, 15))
    
    input_frame = tk.Frame(input_container, bg=bg_input, relief="flat", bd=1, 
                          highlightbackground=border_color, highlightthickness=1)
    input_frame.pack(fill="x", pady=0)
    
    # Поле ввода
    text_input = tk.Entry(input_frame, 
                          font=("Segoe UI", 13), 
                          bd=0, 
                          relief="flat", 
                          bg=bg_input, 
                          fg=text_primary, 
                          insertbackground=accent_blue)
    text_input.pack(side="left", padx=18, pady=14, fill="x", expand=True)
    text_input.bind("<Return>", process_request)
    text_input.bind("<FocusIn>", lambda e: input_frame.config(highlightbackground=accent_blue))
    text_input.bind("<FocusOut>", lambda e: input_frame.config(highlightbackground=border_color))
    
    # Placeholder текст
    placeholder_text = "Сұрағыңызды енгізіңіз..."
    text_input.insert(0, placeholder_text)
    text_input.config(fg=text_muted)
    
    def on_entry_focus_in(e):
        if text_input.get() == placeholder_text:
            text_input.delete(0, tk.END)
            text_input.config(fg=text_primary)
        input_frame.config(highlightbackground=accent_blue)
    
    def on_entry_focus_out(e):
        if not text_input.get():
            text_input.insert(0, placeholder_text)
            text_input.config(fg=text_muted)
        input_frame.config(highlightbackground=border_color)
    
    text_input.bind("<FocusIn>", on_entry_focus_in)
    text_input.bind("<FocusOut>", on_entry_focus_out)
    
    # Кнопки действий
    button_container = tk.Frame(input_frame, bg=bg_input)
    button_container.pack(side="right", padx=(5, 12), pady=10)
    
    send_button = create_icon_button(button_container, "➤", process_request, accent_blue, accent_hover, 42)
    send_button.pack(side="left", padx=4)
    
    browser_button = create_icon_button(button_container, "🌐", open_free_chatgpt, bg_light, accent_blue, 42)
    browser_button.pack(side="left", padx=4)
    
    mic_button = create_icon_button(button_container, "🎤", start_or_stop_assistant, "#E74C3C", "#C0392B", 42)
    mic_button.pack(side="left", padx=4)
    
    # Быстрые кнопки (улучшенный дизайн)
    quick_buttons_frame = tk.Frame(window, bg=bg_dark)
    quick_buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    quick_label = tk.Label(quick_buttons_frame, 
                          text="⚡ Жылдам әрекеттер", 
                          font=("Segoe UI", 11, "bold"), 
                          fg=text_primary, 
                          bg=bg_dark)
    quick_label.pack(anchor="w", pady=(0, 12))
    
    buttons_row = tk.Frame(quick_buttons_frame, bg=bg_dark)
    buttons_row.pack(fill="x")
    
    create_image_button = create_rounded_button(buttons_row, "🖼️ Фото", ask_for_image_prompt, accent_purple, "#8E44AD", 115, 42)
    create_image_button.pack(side="left", padx=(0, 10))
    
    hello_button = create_rounded_button(buttons_row, "👋 Сәлем", respond_to_hello, accent_green, "#229954", 115, 42)
    hello_button.pack(side="left", padx=(0, 10))
    
    weather_button = create_rounded_button(buttons_row, "🌤️ Ауа райы", 
                                          lambda: process_request_with_text("ауа райы"), 
                                          accent_orange, "#E67E22", 115, 42)
    weather_button.pack(side="left", padx=(0, 10))
    
    # Вторая строка быстрых кнопок для приложений
    apps_row = tk.Frame(quick_buttons_frame, bg=bg_dark)
    apps_row.pack(fill="x", pady=(10, 0))
    
    spotify_button = create_rounded_button(apps_row, "🎵 Spotify", launch_spotify, "#1DB954", "#1ED760", 115, 42)
    spotify_button.pack(side="left", padx=(0, 10))
    
    steam_button = create_rounded_button(apps_row, "🎮 Steam", launch_steam, "#171A21", "#1B2838", 115, 42)
    steam_button.pack(side="left", padx=(0, 10))
    
    chrome_button = create_rounded_button(apps_row, "🌐 Chrome", launch_chrome, "#4285F4", "#34A853", 115, 42)
    chrome_button.pack(side="left", padx=(0, 10))
    
    # GIF анимация
    gif_path = r"C:\Users\As\Desktop\Nur_assist\ECNv.gif"
    gif_frames = []
    try:
        gif_image = Image.open(gif_path)
        while True:
            frame = gif_image.copy()
            frame = frame.resize((570, 50))
            gif_frames.append(ImageTk.PhotoImage(frame))
            gif_image.seek(len(gif_frames))
    except (EOFError, FileNotFoundError):
        pass
    
    gif_index = 0
    gif_animation_running = False
    gif_label = tk.Label(window, bg=bg_dark)
    
    # Приветственное сообщение
    welcome_msg = "👋 Сәлем! Мен Felix. Сізге қалай көмектесе аламын? Мені 'Felix' деп шақырыңыз."
    user_dialog.insert("1.0", f"Felix: {welcome_msg}\n", "assistant_message")
    
    # Автоматически запускаем постоянное прослушивание
    global listening_thread, is_listening
    is_listening = True
    listening_thread = threading.Thread(target=listen_for_activation, daemon=True)
    listening_thread.start()
    
    window.mainloop()

assistant_active = False
assistant_thread = None

def start_gif_animation():
    global gif_animation_running
    gif_animation_running = True
    gif_label.pack(side="bottom")
    animate_gif()

def stop_gif_animation():
    global gif_animation_running
    gif_animation_running = False
    gif_label.pack_forget()

def animate_gif():
    global gif_index, gif_frames, gif_animation_running
    if gif_animation_running:
        gif_label.config(image=gif_frames[gif_index])
        gif_index = (gif_index + 1) % len(gif_frames)
        window.after(10, animate_gif)

if __name__ == "__main__":
    create_interface()