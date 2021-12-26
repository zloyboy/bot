import os
import datetime
import pytz
import db
import aiogram
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


cntAll, cntYes, cntNo = 0, 0, 0
ages = ['до 20', '20-29', '30-39', '40-49', '50-59', '60 +']
ageGroup = {ages[0]: '15', ages[1]: '25', ages[2]: '35', ages[3]: '45', ages[4]: '55', ages[5]: '65'}
user_age = {}

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

async def _send_stat(bot: Bot, id: int):
    global cntAll, cntYes, cntNo
    perYes = cntYes / cntAll * 100
    perNo = cntNo / cntAll * 100
    await bot.send_message(id,
        'Независимая статистика по COVID-19' +
        '\nОпрошено: ' + str(cntAll) +
        '\n' + _make_bar(perYes) + ' {:.2f}'.format(perYes) + '%' + ' переболело: ' + str(cntYes) +
        '\n' + _make_bar(perNo) + ' {:.2f}'.format(perNo) + '%' +  ' не болело: ' + str(cntNo))

def _make_stat():
    global cntAll, cntYes, cntNo
    perYes = cntYes / cntAll * 100
    perNo = cntNo / cntAll * 100
    return 'Независимая статистика по COVID-19\nОпрошено: ' + str(cntAll) +\
        '\n' + _make_bar(perYes) + ' {:.2f}'.format(perYes) + '%' + ' переболело: ' + str(cntYes) +\
        '\n' + _make_bar(perNo) + ' {:.2f}'.format(perNo) + '%' +  ' не болело: ' + str(cntNo)

@dp.message_handler()
async def start(message: types.Message):
    global ages, ageGroup, user_age, bot
    id = message.from_user.id
    if id in user_age.keys():
        # get age - send res question
        if user_age[id] == 0:
            age = message.text
            print('age', age)
            if age in ages:
                user_age[id] = int(ageGroup[age])
                keyboard = types.InlineKeyboardMarkup()
                key_yes = types.InlineKeyboardButton(text = 'Да', callback_data = '1')
                key_no = types.InlineKeyboardButton(text = 'Нет', callback_data = '0')
                keyboard.add(key_yes, key_no)
                await bot.send_message(message.chat.id, 'Вы переболели covid19?', reply_markup=keyboard)
            else:
                await bot.send_message(message.chat.id, 'Произошла ошибка: неверный возраст ' + age)
        else:
            await bot.send_message(message.chat.id, 'Произошла ошибка сервера')
    else:
        # new user - send age question
        idname = db.check_id_name(id)
        if idname is None:
            user_age[id] = 0
            keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            key_15 = types.KeyboardButton(ages[0])
            key_25 = types.KeyboardButton(ages[1])
            key_35 = types.KeyboardButton(ages[2])
            key_45 = types.KeyboardButton(ages[3])
            key_55 = types.KeyboardButton(ages[4])
            key_65 = types.KeyboardButton(ages[5])
            keyboard.add(key_15, key_25, key_35, key_45, key_55, key_65)
            await bot.send_message(message.chat.id, 'Независимый подсчет статистики по COVID-19\nУкажите вашу возрастную группу:', reply_markup=keyboard)
        else:
            await bot.send_message(message.chat.id, f'Вы уже приняли участие в подсчете под ником {idname[1]}')
            await bot.send_message(message.chat.id, _make_stat())

@dp.callback_query_handler()
async def button_res(call: types.CallbackQuery):
    # write button data to DB
    global cntAll, cntYes, cntNo, user_age, bot
    res = call.data
    id = call.from_user.id
    name = call.from_user.first_name
    if name is None:
        name = ""
    if db.new_id(id):
        print('insert id', id, 'name', name, 'age', user_age[id], 'res', res)
        db.insert("user", {
        "id": id,
        "created": _get_now_formatted(),
        "name": name,
        "age": user_age[id],
        "res": int(res)
        })
        del user_age[id]
        cntAll = db.count_users()[0]
        cntYes = db.count_res()[0]
        cntNo = cntAll - cntYes
        await bot.send_message(call.message.chat.id, _make_stat())
    else:
        await bot.send_message(call.message.chat.id, 'Произошла ошибка: повторный ввод')


cntAll = db.count_users()[0]
cntYes = db.count_res()[0]
cntNo = cntAll - cntYes

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
