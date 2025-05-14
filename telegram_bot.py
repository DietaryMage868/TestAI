# Телеграм-бот с одной WebApp-кнопкой для запуска мини-приложения
# Перед запуском установите pyTelegramBotAPI: pip install pyTelegramBotAPI
import os
import telebot
from telebot import types

API_TOKEN = os.environ.get('API_TOKEN', 'YOUR_BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            'Открыть мини-приложение',
            web_app=types.WebAppInfo(url='https://testai-git-main-dietarymage868s-projects.vercel.app')
        )
    )
    bot.send_message(
        message.chat.id,
        'Привет! Открой мини-приложение 👇',
        reply_markup=markup
    )

if __name__ == '__main__':
    bot.polling(none_stop=True)
