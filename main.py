import os
import telebot
from telebot import types
import datetime
import pytz
import db

cntAll, cntYes, cntNo = 0, 0, 0

def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return _get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")

def _get_now_datetime() -> datetime.datetime:
    """Возвращает сегодняшний datetime с учётом времненной зоны Мск."""
    tz = pytz.timezone("Europe/Moscow")
    now = datetime.datetime.now(tz)
    return now

def _make_bar(val: float) -> str:
    out = ''
    if 0 < val < 100:
        cnt = round(val) // 5
        out += '|'*cnt
        out += '*'*(20 - cnt)
    return out

def _send_stat(bot: telebot.TeleBot, id: int):
    global cntAll, cntYes, cntNo
    perYes = cntYes / cntAll * 100
    perNo = cntNo / cntAll * 100
    bot.send_message(id,
        'Опрошено: ' + str(cntAll) +
        '\n' + _make_bar(perYes) + ' {:.2f}'.format(perYes) + '%' + ' переболело: ' + str(cntYes) +
        '\n' + _make_bar(perNo) + ' {:.2f}'.format(perNo) + '%' +  ' не болело: ' + str(cntNo)) 


API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
bot = telebot.TeleBot(token=API_TOKEN)

@bot.message_handler(content_types = ['text'])
def get_text(message: types.Message):
    id = message.from_user.id
    if db.new_id(id):
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text = 'Да', callback_data = '1')
        key_no = types.InlineKeyboardButton(text = 'Нет', callback_data = '0')
        keyboard.add(key_yes, key_no)
        bot.send_message(message.chat.id, 'Вы переболели covid19?', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Вы уже приняли участие в глосовании')
        _send_stat(bot, message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def answer(call: types.CallbackQuery):
    global cntAll, cntYes, cntNo
    id = call.from_user.id
    if db.new_id(id):
        print('insert id ', id)
        db.insert("user", {
        "id": id,
        "created": _get_now_formatted(),
        "res": int(call.data)
        })
        cntAll = db.count_users()[0]
        cntYes = db.count_res()[0]
        cntNo = cntAll - cntYes
    else:
        bot.send_message(call.message.chat.id, 'Вы уже приняли участие в глосовании')
    _send_stat(bot, call.message.chat.id)


cntAll = db.count_users()[0]
cntYes = db.count_res()[0]
cntNo = cntAll - cntYes

bot.polling(none_stop = True, interval = 0)
