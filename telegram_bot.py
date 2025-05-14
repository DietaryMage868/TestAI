# Телеграм-бот с реферальной системой на pyTelegramBotAPI
# Перед запуском установите библиотеку: pip install pyTelegramBotAPI
# Замените 'YOUR_BOT_TOKEN' на токен вашего бота

import telebot
from telebot import types
from random import choice as rnd_choice
import string, random

API_TOKEN = '7944260577:AAH0gA7Fo7xvep_h5zjoyQ1Ilzo-g0QK-zY'
bot = telebot.TeleBot(API_TOKEN)

# Простая база для хранения рефералов (в памяти)
users = {}
referrals = {}

# Добавим поддерживаемые валюты
CURRENCIES = ['BTC', 'ETH', 'USDT']
user_balances = {}  # user_id: {currency: amount}
user_wallets = {}   # user_id: {currency: fake_wallet}

# Генерация фейк-кошелька
def generate_wallet():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Открыть мини-приложение', web_app=types.WebAppInfo(url='https://testai-git-main-dietarymage868s-projects.vercel.app')))
    bot.send_message(message.chat.id, 'Привет! Открой мини-приложение 👇', reply_markup=markup)

bot.polling(none_stop=True)
