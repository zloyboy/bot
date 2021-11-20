#import logging
import os

import aiohttp
from aiogram import Bot, Dispatcher, executor, types




#logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
#ACCESS_ID = os.getenv("TELEGRAM_ACCESS_ID")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
#dp.middleware.setup(AccessMiddleware(ACCESS_ID))

@dp.message_handler(commands=['start', 'help'])
async def start_command(message: types.Message):
    await message.answer("Hello!!!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
