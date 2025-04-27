import logging
import os
from dotenv import load_dotenv  # Импортируем для загрузки переменных из .env
from aiogram import Bot, Dispatcher, types
from aiogram.client import Application
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram import F
import asyncio

# Загружаем переменные из .env
load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')  # Получаем токен из переменной окружения
ADMIN_ID = int(os.getenv('ADMIN_ID', '894031843'))  # Получаем ID администратора

if not API_TOKEN:
    raise ValueError("API_TOKEN не найден в .env файле!")

logging.basicConfig(level=logging.INFO)

# Создаем объект приложения
app = Application.builder().token(API_TOKEN).build()

# Используем MemoryStorage для хранения состояний
storage = MemoryStorage()

# Создаем клавиатуру главного меню
menu_keyboard = InlineKeyboardMarkup(row_width=2)
menu_keyboard.add(
    InlineKeyboardButton("Подать заявку", callback_data='submit_application'),
    InlineKeyboardButton("FAQ", callback_data='faq'),
    InlineKeyboardButton("Поддержка", callback_data='support')
)

# Клавиатура для ответа на заявки
application_response_keyboard = InlineKeyboardMarkup(row_width=2)
application_response_keyboard.add(
    InlineKeyboardButton("✅ Принять", callback_data='accept_application'),
    InlineKeyboardButton("❌ Отклонить", callback_data='reject_application')
)

user_applications = {}

class ApplicationForm(StatesGroup):
    waiting_for_application = State()

# Обработчик команды /start
@app.message(F.command('start'))
async def send_welcome(message: types.Message):
    await message.answer_sticker('CAACAgIAAxkBAAEEZPZlZPZxvLrk9l8h2jEXAMPLE')
    await message.answer(
        """👋 Добро пожаловать! 🌟
        
Я ваш личный помощник.
Выберите, что вам нужно:""",
        reply_markup=menu_keyboard
    )

# Обработчик команды /admin
@app.message(F.command('admin'))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total = len(user_applications)
        await message.answer(f"""📊 Панель администратора:
Всего заявок: {total}""")
    else:
        await message.answer("⚠️ У вас нет доступа к этой команде.")

# Обработчик callback_query
@app.callback_query(F.data)
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

# Обработчик текстовых сообщений для заявки
@app.message(ApplicationForm.waiting_for_application, content_types=types.ContentTypes.TEXT)
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

# Обработчик на случай, если бот не понимает команду
@app.message()
async def fallback(message: types.Message):
    await message.reply("❓ Я вас не понял. Пожалуйста, используйте команды или нажмите /start для начала.")

# Основная функция для запуска бота
async def main():
    try:
        # Запускаем бота
        await app.start_polling()
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    asyncio.run(main())
