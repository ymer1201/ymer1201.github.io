import telebot
import subprocess
import os
import signal
import logging
import schedule
import time
from datetime import datetime
from telebot import types
import threading
import platform
import atexit

# Токен вашего бота
TOKEN = "7840921830:AAGIRbqhuuAr8qyfX_br-0stFxAAdCGF6R8"  # Замените на токен вашего бота
bot = telebot.TeleBot(TOKEN)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Множество активных процессов
active_processes = {}

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🚀 Привет! Отправь мне код или файл, и я выполню его.")

# Функция для выполнения кода
def run_code(user_id, code):
    try:
        # Проверка платформы
        if platform.system() == 'Windows':
            process = subprocess.Popen(
                ['python', '-c', code],  # Используем 'python' вместо 'python3' на Windows
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        else:
            process = subprocess.Popen(
                ['python3', '-c', code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # Используем только на Unix-подобных системах
            )

        active_processes[user_id] = process
        stdout, stderr = process.communicate()
        output = stdout.strip() or "✅ Код выполнен без вывода."
        error = stderr.strip() or "✅ Ошибок нет."

        bot.send_message(user_id, f"📤 Результат:\n{output}\n🚨 Ошибки:\n{error}")
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка при выполнении кода: {e}")

# Обработчик для кода в сообщении
@bot.message_handler(func=lambda message: True)
def handle_code(message):
    user_id = message.chat.id
    code = message.text

    bot.send_message(user_id, "⏳ Выполняю код...")
    run_code(user_id, code)

# Обработчик для файлов
@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.chat.id
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Сохраняем файл временно
    file_name = message.document.file_name
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    # Читаем содержимое файла
    with open(file_name, 'r') as file:
        code = file.read()

    # Удаляем временный файл
    os.remove(file_name)

    bot.send_message(user_id, "⏳ Выполняю код из файла...")
    run_code(user_id, code)

# Обработчик для остановки кода через инлайн-кнопку
@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def stop_code(call):
    user_id = int(call.data.split("_")[1])

    if user_id in active_processes:
        process = active_processes[user_id]
        os.killpg(process.pid, signal.SIGTERM)  # Отправляем сигнал для завершения процесса
        del active_processes[user_id]
        bot.answer_callback_query(call.id, "⏹️ Код остановлен.")
        bot.send_message(user_id, "❌ Выполнение кода остановлено.")
    else:
        bot.answer_callback_query(call.id, "⚠️ Нет активного процесса.")

# Обработчик команды /stop для остановки процесса
@bot.message_handler(commands=['stop'])
def stop_code_global(message):
    user_id = message.chat.id
    if user_id in active_processes:
        process = active_processes[user_id]
        os.killpg(process.pid, signal.SIGTERM)
        del active_processes[user_id]
        bot.send_message(user_id, "❌ Все процессы были остановлены.")
    else:
        bot.send_message(user_id, "⚠️ Нет активных процессов для остановки.")

# Завершение всех процессов при выходе
def cleanup():
    for user_id, process in active_processes.items():
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except Exception as e:
            logger.error(f"Ошибка при завершении процесса: {e}")

atexit.register(cleanup)

# Запуск бота
def start_bot():
    print("=== БОТ ЗАПУЩЕН ===")
    bot.infinity_polling()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True  # Поток завершится вместе с основным потоком
    bot_thread.start()

    while True:
        schedule.run_pending()
        time.sleep(1)