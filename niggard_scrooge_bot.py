import time
import requests
import json
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
import json
import requests
import telebot
from telebot import types

#------------------------------------------------------Функции связанные с ТГ ботом  
#создаем объект класса ТелеБот с именем bot
bot = telebot.TeleBot(api_key)

# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start"])
def start(m, res=False):
    bot.send_message(m.chat.id, 'Бот передает текущий курс обмена на киви и самое дешевое предложение на покупку тенге')

#---------------------------------------Функции связанные с функцией выбора просматриваемого курса  
@bot.message_handler(commands=["check_currency"])
def check_valuta(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Тенге ₸")
    btn2 = types.KeyboardButton("Рубли ₽")
    markup.add(btn1, btn2)
    msg = bot.send_message(m.chat.id, "Выберите курс какой валюты вы хотите узнать", reply_markup = markup)
    bot.register_next_step_handler(msg, check_payment_system)


def check_payment_system(m):
    currency_result = []
    if (m.text == "Тенге ₸"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        currency_result.append("KZT")
        btn1 = types.KeyboardButton("QIWI")
        markup.add(btn1)
        msg = bot.send_message(m.chat.id, "Выберите платежную систему", reply_markup = markup)
        bot.register_next_step_handler(msg, check_trade_type, currency_result)

    elif (m.text == "Рубли ₽"):
        currency_result.append("RUB")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("QIWI")
        btn2 = types.KeyboardButton("Payeer")
        btn3 = types.KeyboardButton("Advcash")
        btn4 = types.KeyboardButton("All")
        markup.add(btn1,btn2,btn3,btn4)
        msg = bot.send_message(m.chat.id, "Выберите платежную систему", reply_markup = markup)
        bot.register_next_step_handler(msg, check_trade_type, currency_result) 

def check_trade_type(m, currency_result):
    currency_result.append(m.text)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("BUY")
    btn2 = types.KeyboardButton("SELL")
    markup.add(btn1,btn2)
    msg = bot.send_message(m.chat.id, "Выберите тип операции", reply_markup = markup)
    bot.register_next_step_handler(msg, check_price_send_message, currency_result)

#Функция отправки пользователю текущей цены
def check_price_send_message(m, currency_result):
    currency_result.append(m.text)
    pay_type = currency_result[1] # первым аргументом получаем платежную систему
    fiat_type = currency_result[0] # тип фиатной валюты, которую будем покупать
    trade_type = currency_result[2] # покупка или продажа
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(m.chat.id, check_price(pay_type,fiat_type,trade_type), reply_markup = markup)
    bot.clear_step_handler_by_chat_id(m)

#Функция отправки пользователю текущего курса обмена
@bot.message_handler(commands=["check_currency"])
def check_currency_message(m, res=False):
    bot.send_message(m.chat.id, 'KZT/RUB: ' + str(check_qiwi_currency("398","643")))

#------------------------------------------------------Функции связанные с парсингом


#функция проверки курса обмена на киви кошельке
def check_qiwi_currency(currency_to, currency_from):
    s = requests.Session()
    s.headers = {'content-type': 'application/json'}
    s.headers['Accept'] = 'application/json'
    res = s.get('https://edge.qiwi.com/sinap/crossRates')

    # все курсы
    rates = res.json()['result']

    # запрошенный курс
    rate = [x for x in rates if x['from'] == currency_from and x['to'] == currency_to]
    if (len(rate) == 0):
        print('No rate for this currencies!')
        return
    else:
        return rate[0]['rate']

def check_price(pay_type, fiat_type, trade_type):
    #массив в который будет записан результат выполнения функции
    data_array = []
    result = ""
    #какую валюту покупаем
    buy_type = "USDT"

    #В зависимости от запроса пользователя меняем в запросе заголовки на наши переменные
    data = {
      "asset": buy_type,
      "fiat": fiat_type,
      "merchantCheck": False,
      "page": 1,
      "payTypes": [pay_type],
      "publisherType": None,
      "rows": 10,
      "tradeType": trade_type
    }

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Length": "123",
        "content-type": "application/json",
        "Host": "p2p.binance.com",
        "Origin": "https://p2p.binance.com",
        "Pragma": "no-cache",
        "TE": "Trailers",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
    }

    r = requests.post('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers=headers, json=data)
    
    #Проверяем есть ли возможность подключиться к апи
    if (r.status_code == 200):
        data = r.json()
        #количество предложений, получаем массив data, смотрим по ключу 'adv'
        offer_count = len(data['data'])
        #символ валюты, смотрю по первому предложению, так как он везде один
        fiat_symbol = data['data'][0]['adv']['fiatSymbol']

        #добавляем в результат информацию по каждому предложению
        for i in range(0, offer_count-1):
            data_array.append(data['data'][i]['adv']['price'])
            #форматируем массив для вывода одним сообщением
            result += data_array[i] + fiat_symbol + '\n'
        result = f'Предложения о {trade_type} (Ограничено десятью первыми предложениями) \n' + result
        return result

#запускаем бота
bot.polling(none_stop=True, interval=0)
