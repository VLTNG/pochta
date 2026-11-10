import imaplib
import email
from email.header import decode_header
import telebot
import time
import re # ОБЯЗАТЕЛЬНО для очистки
imaplib.Commands['ID'] = ('NONAUTH', 'AUTH') 

# --- НАСТРОЙКИ TELEGRAM ---
TELEGRAM_TOKEN = "__________________"
CHAT_ID = "_____________" # Узнать можно у бота @userinfobot

# --- СПИСОК ПОЧТ ---
ACCOUNTS = [
    {
        "name": "_______________",
        "server": "_______________",
        "login": "_______________",
        "password": "_______________"
    },
   {
        "name": "_______________",
        "server": "_______________",
        "login": "_______________",
        "password": "_______________"
    },
    {
        "name": "_______________",
        "server": "_______________",
        "login": "_______________",
        "password": "_______________"
    }
]

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def send_telegram_msg(text):
    """Безопасная отправка, чтобы скрипт не падал, если нет VPN"""
    try:
        bot.send_message(CHAT_ID, text)
    except Exception as e:
        print(f"  [!] Ошибка Telegram (нет VPN?): Не удалось отправить.")

def check_account(account):
    print(f"Проверяем: {account['name']}...")
    try:
        # МАГИЯ ОЧИСТКИ: Удаляем ВСЁ, кроме английских букв, цифр и знаков @ . - _
        clean_login = re.sub(r'[^a-zA-Z0-9@\.\-_]', '', str(account['login']))
        clean_password = re.sub(r'[^a-zA-Z0-9]', '', str(account['password']))
        
        # Выводим в консоль, чтобы вы видели, что реально уходит на сервер
        print(f"  [Отладка] Логин: {clean_login}")

        mail = imaplib.IMAP4_SSL(account['server'])
        mail._encoding = 'utf-8' 
        
        # Фикс для Mail.ru
        if "mail.ru" in account['server']:
            args = ("name", "my_client", "version", "1.0", "vendor", "my_python_script")
            mail._simple_command('ID', '("' + '" "'.join(args) + '")')
            
        # ЛОГИНИМСЯ ОЧИЩЕННЫМИ ДАННЫМИ
        mail.login(clean_login, clean_password)
        mail.select("inbox")

        status, messages = mail.search(None, 'UNSEEN')
        if status != "OK":
            return

        mail_ids = messages[0].split()
        
        if len(mail_ids) > 0:
            latest_email_id = mail_ids[-1]
            status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                        
                    sender = msg.get("From")
                    text = f"📬 [{account['name']}]\n\nОт: {sender}\nТема: {subject}"
                    
                    send_telegram_msg(text)
                    print(f"  -> Найдено новое письмо!")
                    
                    mail.store(latest_email_id, '+FLAGS', '\\Seen')
        else:
            print(f"  -> Новых писем нет.")
            
        mail.logout()
    except Exception as e:
        print(f"  -> ОШИБКА при проверке {account['name']}: {e}")

# Бесконечный цикл
while True:
    print("--- НАЧАЛО ПРОВЕРКИ ---")
    for acc in ACCOUNTS:
        check_account(acc)
    print("--- ЖДЕМ 1 МИНУТУ ---\n")
    time.sleep(60)