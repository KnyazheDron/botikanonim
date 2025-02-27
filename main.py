from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters, CallbackQueryHandler
import secrets
from config import TOKEN  # Импорт токена из config.py

# Словарь для хранения уникальных ссылок и ID пользователей
user_links = {}

# Обратный словарь для хранения ID пользователей и их токенов (чтобы удалять старые ссылки)
user_tokens = {}

# Генерация уникальной ссылки
def generate_link(user_id: int) -> str:
    # Если у пользователя уже есть токен, удаляем старую ссылку
    if user_id in user_tokens:
        old_token = user_tokens[user_id]
        del user_links[old_token]  # Удаляем старую ссылку
        del user_tokens[user_id]  # Удаляем старый токен

    # Генерация нового токена
    token = secrets.token_hex(8)  # Генерация уникального токена
    user_links[token] = user_id   # Связываем токен с ID пользователя
    user_tokens[user_id] = token  # Сохраняем токен для пользователя
    return f"https://t.me/MyAnonymousBot?start={token}"  # Замените MyAnonymousBot на username вашего бота

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    args = context.args

    if args:
        # Если пользователь перешел по ссылке
        token = args[0]
        if token in user_links:
            # Сохраняем ID пользователя, который задает вопрос
            context.user_data['target_user_id'] = user_links[token]
            await update.message.reply_text(
                "Вы можете отправить анонимное сообщение. Напишите его ниже:"
            )
        else:
            await update.message.reply_text("Неверная ссылка.")
    else:
        # Если это владелец канала
        link = generate_link(user_id)
        await update.message.reply_text(
            f"Ваша уникальная ссылка для анонимных вопросов:\n\n{link}\n\n"
            "Поделитесь этой ссылкой, чтобы получать вопросы."
        )

# Обработка анонимных сообщений
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text

    if 'target_user_id' in context.user_data:
        # Если это анонимное сообщение
        target_user_id = context.user_data['target_user_id']
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f" Новое анонимное сообщение:\n\n{text}"
        )

        # Создаем кнопки
        keyboard = [
            [InlineKeyboardButton("Отправить ещё сообщение", callback_data='send_again')],
            [InlineKeyboardButton("В меню", callback_data='to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем сообщение с кнопками
        await update.message.reply_text("Ваше сообщение отправлено анонимно!", reply_markup=reply_markup)
    else:
        # Если это обычное сообщение
        await update.message.reply_text("Используйте ссылку, чтобы задать вопрос.")

# Обработка нажатий на кнопки
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == 'send_again':
        # Пользователь хочет отправить еще одно сообщение
        await query.edit_message_text("Напишите ваше следующее анонимное сообщение:")
    elif query.data == 'to_menu':
        # Пользователь хочет вернуться в меню
        link = generate_link(user_id)
        await query.edit_message_text(
            f"Ваша уникальная ссылка для анонимных вопросов:\n\n{link}\n\n"
            "Поделитесь этой ссылкой, чтобы получать вопросы."
        )

# Основная функция
def main() -> None:
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))  # Обработчик кнопок

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()