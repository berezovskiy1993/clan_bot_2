import logging
import re
import os
from aiogram import types, F
from aiogram import Application
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '894031843'))

logging.basicConfig(level=logging.INFO)

# Создаем объект Application
application = Application.builder().token(API_TOKEN).storage(MemoryStorage()).build()

class ApplicationForm(StatesGroup):
    waiting_for_application = State()

# Главное меню с кнопками
menu_keyboard = InlineKeyboardMarkup(row_width=2)
menu_keyboard.add(
    InlineKeyboardButton("Подать заявку", callback_data='submit_application'),
    InlineKeyboardButton("FAQ", callback_data='faq'),
    InlineKeyboardButton("Поддержка", callback_data='support')
)

# Кнопки для администратора
application_response_keyboard = InlineKeyboardMarkup(row_width=2)
application_response_keyboard.add(
    InlineKeyboardButton("✅ Принять", callback_data='accept_application'),
    InlineKeyboardButton("❌ Отклонить", callback_data='reject_application')
)

user_applications = {}

# Обработка команды /start
@application.message(F.command('start'))
async def send_welcome(message: types.Message):
    await message.answer_sticker('CAACAgIAAxkBAAEEZPZlZPZxvLrk9l8h2jEXAMPLE')
    await message.answer(
        """👋 Добро пожаловать! 🌟
        
Я ваш личный помощник.
Выберите, что вам нужно:""",
        reply_markup=menu_keyboard
    )

# Обработка команды /admin
@application.message(F.command('admin'))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total = len(user_applications)
        await message.answer(f"""📊 Панель администратора:
Всего заявок: {total}""")
    else:
        await message.answer("⚠️ У вас нет доступа к этой команде.")

# Обработка callback-запросов
@application.callback_query(F.data)
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    code = callback_query.data
    if code == 'submit_application':
        await callback_query.answer()
        await application.bot.send_message(callback_query.from_user.id, "📝 Пожалуйста, напишите свое имя и номер телефона:")
        await ApplicationForm.waiting_for_application.set()
    elif code == 'faq':
        text = """🔍 Часто задаваемые вопросы:
• Как работает бот?
• Как оформить заявку?
• Как связаться с поддержкой?"""
        await callback_query.answer()
        await application.bot.send_message(callback_query.from_user.id, text)
    elif code == 'support':
        text = "😊 Для связи с нашей поддержкой напишите: @SupportUsername"
        await callback_query.answer()
        await application.bot.send_message(callback_query.from_user.id, text)
    elif code == 'accept_application':
        await callback_query.answer()
        await application.bot.send_message(callback_query.from_user.id, "✅ Заявка принята!")
    elif code == 'reject_application':
        await callback_query.answer()
        await application.bot.send_message(callback_query.from_user.id, "❌ Заявка отклонена.")
    else:
        text = "⚠️ Неизвестная команда."
        await callback_query.answer()
        await application.bot.send_message(callback_query.from_user.id, text)

# Обработка заявки
@application.message(ApplicationForm.waiting_for_application, content_types=types.ContentTypes.TEXT)
async def process_application(message: types.Message, state: FSMContext):
    user_data = message.text
    phone_pattern = re.compile(r'\+?\d{10,15}')
    if not phone_pattern.search(user_data):
        await message.reply("⚠️ Пожалуйста, укажите корректный номер телефона!")
        return
    user_applications[message.from_user.id] = user_data
    await application.bot.send_message(message.chat.id, "✅ Спасибо! Ваша заявка отправлена.")
    await application.bot.send_message(
        ADMIN_ID,
        f"""🗓️ Новая заявка от @{message.from_user.username or message.from_user.id}:
{user_data}
ID пользователя: {message.from_user.id}""",
        reply_markup=application_response_keyboard
    )
    await state.clear()

# Обработка нераспознанных сообщений
@application.message()
async def fallback(message: types.Message):
    await message.reply("❓ Я вас не понял. Пожалуйста, используйте команды или нажмите /start для начала.")

# Основной цикл
async def main():
    try:
        # Запуск бота
        await application.start_polling()
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    # Запуск через asyncio
    asyncio.run(main())
