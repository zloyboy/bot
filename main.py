import os
import telebot
from telebot import types
import datetime
import pytz
import db

userId = 0

cntAll, cntYes, cntNo = 0, 0, 0
ages = ['до 20', '20-29', '30-39', '40-49', '50-59', '60 + ']
ageGroup = {ages[0]: '15', ages[1]: '25', ages[2]: '35', ages[3]: '45', ages[4]: '55', ages[5]: '65'}

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
    if 0 <= val <= 100:
        cnt = round(val) // 5
        out += '|'*cnt
        out += '*'*(20 - cnt)
    return out

def _send_stat(bot: telebot.TeleBot, id: int):
    global cntAll, cntYes, cntNo
    perYes = cntYes / cntAll * 100
    perNo = cntNo / cntAll * 100
    bot.send_message(id,
        'Независимая статистика по COVID-19' +
        '\nОпрошено: ' + str(cntAll) +
        '\n' + _make_bar(perYes) + ' {:.2f}'.format(perYes) + '%' + ' переболело: ' + str(cntYes) +
        '\n' + _make_bar(perNo) + ' {:.2f}'.format(perNo) + '%' +  ' не болело: ' + str(cntNo)) 


API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
bot = telebot.TeleBot(token=API_TOKEN)

# handle any text input, to send age question
@bot.message_handler(content_types = ['text'])
def get_text(message: types.Message):
    global ages
    #id = message.from_user.id
    #idname = db.check_id_name(id)
    #if idname is None:
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    key_15 = types.KeyboardButton(ages[0])
    key_25 = types.KeyboardButton(ages[1])
    key_35 = types.KeyboardButton(ages[2])
    key_45 = types.KeyboardButton(ages[3])
    key_55 = types.KeyboardButton(ages[4])
    key_65 = types.KeyboardButton(ages[5])
    keyboard.add(key_15, key_25, key_35, key_45, key_55, key_65)
    msg = bot.send_message(message.chat.id, 'Независимый подсчет статистики по COVID-19\nУкажите вашу возрастную группу:', reply_markup=keyboard)
    bot.register_next_step_handler(msg, age_button)
    #else:
    #    bot.send_message(message.chat.id, f'Вы уже приняли участие в подсчете под ником {idname[1]}')
    #    _send_stat(bot, message.chat.id)

# handle age answer
def age_button(message: types.Message):
    global ages, ageGroup
    age = message.text
    #print(age)
    if age in ages:
        data_yes = '1,' + ageGroup[age]
        data_no = '0,' + ageGroup[age]
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text = 'Да', callback_data = data_yes)
        key_no = types.InlineKeyboardButton(text = 'Нет', callback_data = data_no)
        keyboard.add(key_yes, key_no)
        bot.send_message(message.chat.id, 'Вы переболели covid19?', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Произошла ошибка: неверный возраст ' + age)

# write button data to DB
@bot.callback_query_handler(func=lambda call: True)
def answer(call: types.CallbackQuery):
    global cntAll, cntYes, cntNo, userId
    #id = call.from_user.id
    name = call.from_user.first_name
    if name is None:
        name = ""
    #if db.new_id(id):
    userId = userId + 1
    ans = call.data.split(',')
    print('insert id', userId, 'name', name, 'age', ans[1], 'res', ans[0])
    db.insert("user", {
    "id": userId,
    "created": _get_now_formatted(),
    "name": name,
    "age": int(ans[1]),
    "res": int(ans[0])
    })
    cntAll = db.count_users()[0]
    cntYes = db.count_res()[0]
    cntNo = cntAll - cntYes
    #else:
    #    bot.send_message(call.message.chat.id, 'Произошла ошибка: повторный ввод')
    _send_stat(bot, call.message.chat.id)


cntAll = db.count_users()[0]
cntYes = db.count_res()[0]
cntNo = cntAll - cntYes

bot.polling(none_stop = True, interval = 0)
