import logging
import asyncio
import os
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
application = Dispatcher()

class ApplicationForm(StatesGroup):
    waiting_for_application = State()

menu_keyboard = InlineKeyboardMarkup(row_width=2)
menu_keyboard.add(
    InlineKeyboardButton("Подать заявку", callback_data='submit_application'),
    InlineKeyboardButton("FAQ", callback_data='faq'),
    InlineKeyboardButton("Поддержка", callback_data='support')
)

application_response_keyboard = InlineKeyboardMarkup(row_width=2)
application_response_keyboard.add(
    InlineKeyboardButton("✅ Принять", callback_data='accept_application'),
    InlineKeyboardButton("❌ Отклонить", callback_data='reject_application')
)

user_applications = {}

@application.message(F.command("start"))
async def send_welcome(message: types.Message):
    await message.answer_sticker('CAACAgIAAxkBAAEEZPZlZPZxvLrk9l8h2jEXAMPLE')
    await message.answer(
        """👋 Добро пожаловать! 🌟

Я ваш личный помощник.
Выберите, что вам нужно:""",
        reply_markup=menu_keyboard
    )

@application.message(F.command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total = len(user_applications)
        await message.answer(f"""📊 Панель администратора:
Всего заявок: {total}""")
    else:
        await message.answer("⚠️ У вас нет доступа к этой команде.")

@application.callback_query(F.data)
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    code = callback_query.data
    user_id = callback_query.from_user.id

    if code == 'submit_application':
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(user_id, "📝 Пожалуйста, напишите свое имя и номер телефона:")
        await state.set_state(ApplicationForm.waiting_for_application)
    elif code == 'faq':
        text = """🔍 Часто задаваемые вопросы:
• Как работает бот?
• Как оформить заявку?
• Как связаться с поддержкой?"""
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(user_id, text)
    elif code == 'support':
        text = "😊 Для связи с нашей поддержкой напишите: @SupportUsername"
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(user_id, text)
    elif code == 'accept_application':
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(user_id, "✅ Заявка принята!")
    elif code == 'reject_application':
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(user_id, "❌ Заявка отклонена.")
    else:
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(user_id, "⚠️ Неизвестная команда.")

@application.message(ApplicationForm.waiting_for_application, F.content_type.in_({'text'}))
async def process_application(message: types.Message, state: FSMContext):
    user_data = message.text
    phone_pattern = re.compile(r'\+?\d{10,15}')
    if not phone_pattern.search(user_data):
        await message.reply("⚠️ Пожалуйста, укажите корректный номер телефона!")
        return
    user_applications[message.from_user.id] = user_data
    await message.reply("✅ Спасибо! Ваша заявка отправлена.")
    await bot.send_message(
        ADMIN_ID,
        f"""🗓️ Новая заявка от @{message.from_user.username or message.from_user.id}:
{user_data}
ID пользователя: {message.from_user.id}""",
        reply_markup=application_response_keyboard
    )
    await state.clear()

@application.message()
async def fallback(message: types.Message):
    await message.reply("❓ Я вас не понял. Пожалуйста, используйте команды или нажмите /start для начала.")

async def main():
    try:
        await application.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    asyncio.run(main())
