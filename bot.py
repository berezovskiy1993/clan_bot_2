import logging
import re
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
from aiogram.fsm.storage.memory import MemoryStorage  # Новый импорт для памяти
from aiogram.fsm.state import State, StatesGroup  # Новый импорт для состояний
from aiogram.fsm.context import FSMContext  # Новый импорт для контекста FSM
import asyncio

API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '894031843'))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()  # Используем новое хранилище
dp = Dispatcher(bot, storage=storage)

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

@dp.message(F.command('start'))  # Используем новый синтаксис для команд
async def send_welcome(message: types.Message):
    await message.answer_sticker('CAACAgIAAxkBAAEEZPZlZPZxvLrk9l8h2jEXAMPLE')
    await message.answer(
        """👋 Добро пожаловать! 🌟
        
Я ваш личный помощник.
Выберите, что вам нужно:""",
        reply_markup=menu_keyboard
    )

@dp.message(F.command('admin'))  # Новый синтаксис для команд
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total = len(user_applications)
        await message.answer(f"""📊 Панель администратора:
Всего заявок: {total}""")
    else:
        await message.answer("⚠️ У вас нет доступа к этой команде.")

@dp.callback_query(F.data)
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    code = callback_query.data
    if code == 'submit_application':
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "📝 Пожалуйста, напишите свое имя и номер телефона:")
        await ApplicationForm.waiting_for_application.set()
    elif code == 'faq':
        text = """🔍 Часто задаваемые вопросы:
• Как работает бот?
• Как оформить заявку?
• Как связаться с поддержкой?"""
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, text)
    elif code == 'support':
        text = "😊 Для связи с нашей поддержкой напишите: @SupportUsername"
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, text)
    elif code == 'accept_application':
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "✅ Заявка принята!")
    elif code == 'reject_application':
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "❌ Заявка отклонена.")
    else:
        text = "⚠️ Неизвестная команда."
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, text)

@dp.message(ApplicationForm.waiting_for_application, content_types=types.ContentTypes.TEXT)
async def process_application(message: types.Message, state: FSMContext):
    user_data = message.text
    phone_pattern = re.compile(r'\+?\d{10,15}')
    if not phone_pattern.search(user_data):
        await message.reply("⚠️ Пожалуйста, укажите корректный номер телефона!")
        return
    user_applications[message.from_user.id] = user_data
    await bot.send_message(message.chat.id, "✅ Спасибо! Ваша заявка отправлена.")
    await bot.send_message(
        ADMIN_ID,
        f"""🗓️ Новая заявка от @{message.from_user.username or message.from_user.id}:
{user_data}
ID пользователя: {message.from_user.id}""",
        reply_markup=application_response_keyboard
    )
    await state.clear()

@dp.message()
async def fallback(message: types.Message):
    await message.reply("❓ Я вас не понял. Пожалуйста, используйте команды или нажмите /start для начала.")

async def main():
    # Запуск бота
    try:
        await dp.start_polling()
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    # Запуск через asyncio
    asyncio.run(main())
