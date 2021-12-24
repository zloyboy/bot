import telebot
from telebot import types
import datetime
import pytz
import db

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
        #out = '|'
        out += '|'*cnt
        out += '_'*(20 - cnt)
        #out += '|'
    return out

bot = telebot.TeleBot('')

@bot.message_handler(content_types = ['text'])
def get_text(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text = 'Да', callback_data = '1')
    key_no = types.InlineKeyboardButton(text = 'Нет', callback_data = '0')
    keyboard.add(key_yes, key_no)
    bot.send_message(message.chat.id, 'Вы переболели covid19?', reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def answer(call: types.CallbackQuery):
    id = call.from_user.id
    if db.new_id(id):
        print('insert id ', id)
        inserted_row_id = db.insert("user", {
        "id": id,
        "created": _get_now_formatted(),
        "res": int(call.data)
        })
    else:
        print('exist id ', id)
    cntAll = db.count_users()[0]
    cntYes = db.count_res()[0]
    cntNo = cntAll - cntYes
    perYes = cntYes / cntAll * 100
    perNo = cntNo / cntAll * 100
    bot.send_message(call.message.chat.id,
        'Опрошено: ' + str(cntAll) +
        '\n' + _make_bar(perYes) + str(perYes) + '%' + ' переболело: ' + str(cntYes) +
        '\n' + _make_bar(perNo) + str(perYes) + '%' +  ' не болело: ' + str(cntNo)) 

bot.polling(none_stop = True, interval = 0)
