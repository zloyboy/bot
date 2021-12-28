import os
import time, datetime, pytz
import db
import aiogram
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


cntAll, cntYes, cntNo = 0, 0, 0
ages = ['до 20', '20-29', '30-39', '40-49', '50-59', '60 ++']
ages_stat = [[0,0], [0,0], [0,0], [0,0], [0,0], [0,0]]
ageGroup = {ages[0]: '15', ages[1]: '25', ages[2]: '35', ages[3]: '45', ages[4]: '55', ages[5]: '65'}
user_age = {}
user_timestamp = {}
repeat_msg = '\nДля повторного показа статистики введите любой текст или нажмите Start, но не ранее чем через 10 секунд'


def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return _get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")

def _get_now_datetime() -> datetime.datetime:
    """Возвращает сегодняшний datetime с учётом времненной зоны Мск."""
    tz = pytz.timezone("Europe/Moscow")
    now = datetime.datetime.now(tz)
    return now

#def _make_bar(val: float) -> str:
#    out = ''
#    if 0 <= val <= 100:
#        cnt = round(val) // 5
#        out += '|'*cnt
#        out += '*'*(20 - cnt)
#    return out

def _read_stat_from_db():
    global cntAll, cntYes, cntNo, ages_stat, db
    cntAll = db.count_users()[0]
    cntYes = db.count_res()[0]
    cntNo = cntAll - cntYes
    for i in range(6):
        ages_stat[i][0] = db.count_age(i*10 + 15)[0]
        if 0 < ages_stat[i][0]:
            ages_stat[i][1] = db.count_age_res(i*10 + 15)[0]

def _make_stat():
    global cntAll, cntYes, cntNo, ages_stat
    perYes = cntYes / cntAll * 100
    perNo = cntNo / cntAll * 100
    perAge = [0, 0, 0, 0, 0, 0]
    outAge = ''
    for i in range(6):
        if 0 < ages_stat[i][0]:
            perAge[i] = ages_stat[i][1] / ages_stat[i][0] * 100
        outAge += '\n' + str(ages[i]) + ' - ' + '{:.2f}'.format(perAge[i]) + '% ' + str(ages_stat[i][1]) + '/' + str(ages_stat[i][0])
    return 'Независимая статистика по COVID-19\nОпрошено: ' + str(cntAll) +\
        '\n' + '{:.2f}'.format(perYes) + '%' + ' переболело: ' + str(cntYes) +\
        '\n' + '{:.2f}'.format(perNo) + '%' +  ' не болело: ' + str(cntNo) +\
        '\nЗаболеваемость по возрастным группам:' + outAge


@dp.message_handler()
async def start(message: types.Message):
    global ages, user_age, bot
    id = message.from_user.id
    # repeat start timeout is 10 sec
    curr_time = int(time.time())
    if id in user_timestamp.keys():
        #print('timeout', curr_time - user_timestamp[id])
        if 10 < curr_time - user_timestamp[id]:
            user_timestamp[id] = curr_time
        else:
            return
    else:
        user_timestamp[id] = curr_time
    idname = db.check_id_name(id)
    if idname is None:
        # new user - send age question
        user_age[id] = 0
        keyboard = types.InlineKeyboardMarkup()
        key_15 = types.InlineKeyboardButton(text=ages[0], callback_data=ages[0])
        key_25 = types.InlineKeyboardButton(text=ages[1], callback_data=ages[1])
        key_35 = types.InlineKeyboardButton(text=ages[2], callback_data=ages[2])
        key_45 = types.InlineKeyboardButton(text=ages[3], callback_data=ages[3])
        key_55 = types.InlineKeyboardButton(text=ages[4], callback_data=ages[4])
        key_65 = types.InlineKeyboardButton(text=ages[5], callback_data=ages[5])
        keyboard.add(key_15, key_25, key_35, key_45, key_55, key_65)
        await bot.send_message(message.chat.id, 'Независимый подсчет статистики по COVID-19\nУкажите вашу возрастную группу:', reply_markup=keyboard)
    else:
        # exist user - send statistic
        await bot.send_message(message.chat.id, f'Вы уже приняли участие в подсчете под именем {idname[1]}' + repeat_msg)
        kbd = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        key_start = types.KeyboardButton('Start')
        kbd.add(key_start)
        await bot.send_message(message.chat.id, _make_stat(), reply_markup=kbd)
        if id in user_age.keys():
            del user_age[id]

@dp.callback_query_handler()
async def button_res(call: types.CallbackQuery):
    global cntAll, cntYes, cntNo, user_age, bot
    id = call.from_user.id
    if id in user_age.keys():
        if user_age[id] == 0:
            # get age - send res question
            age = call.data
            if age in ages:
                user_age[id] = int(ageGroup[age])
                keyboard = types.InlineKeyboardMarkup()
                key_yes = types.InlineKeyboardButton(text = 'Да', callback_data = '1')
                key_no = types.InlineKeyboardButton(text = 'Нет', callback_data = '0')
                keyboard.add(key_yes, key_no)
                await bot.send_message(call.message.chat.id, 'Вы переболели covid19?\n(по официальному мед.заключению)', reply_markup=keyboard)
                return
            else:
                await bot.send_message(call.message.chat.id, 'Произошла ошибка: неверный возраст ' + age)
        else:
            # write poll results to DB
            outMsg = 'Произошла ошибка: повторный ввод'
            res = call.data
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
                _read_stat_from_db()
                outMsg = _make_stat()
            await bot.send_message(call.message.chat.id, outMsg)
            kbd = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            key_start = types.KeyboardButton('Start')
            kbd.add(key_start)
            await bot.send_message(call.message.chat.id, repeat_msg, reply_markup=kbd)
        del user_age[id]
    else:
        await bot.send_message(call.message.chat.id, 'Произошла ошибка сервера')


_read_stat_from_db()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
