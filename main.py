import os.path

from peewee import DoesNotExist
from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, \
    ReplyKeyboardRemove

from config import Config
from models import Product

LOCKED_CONFIG_PARAMS = [
    "bot_token"
]

HIDDEN_CONFIG_PARAMS = [
    "bot_token"
]

MAIN_MENU = ReplyKeyboardMarkup(resize_keyboard=True)
MAIN_MENU.row("📁 База товарів", "📝 Генератор постів")


def generate_post(product_name):
    template = "🤍 {}\n\n" \
               "▫️Срібло 925 проби\n" \
               "▫️За наявністю розмірів в дірект\n" \
               "▫️Безкоштовна доставка по Тернополю \n\n" \
               "💸 Ціна в дірект\n\n" \
               "#pandora"
    return template.format(product_name)


def generate_iterator_keyboard(product_id):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("◀️", callback_data=f"show {product_id - 1}"),
        InlineKeyboardButton("❌", callback_data=f"close"),
        InlineKeyboardButton("▶️", callback_data=f"show {product_id + 1}")
    )
    return markup


def main():
    Product.create_table()
    if not os.path.exists("images"):
        os.mkdir("images")

    authorized_users = []
    authorized_admins = []

    bot = TeleBot(Config.get_instance().get("bot_token"), parse_mode="HTML")

    @bot.message_handler(commands=["start"], chat_types=["private"])
    def _start(message: Message):
        if message.from_user.id not in authorized_users:
            bot.send_message(message.chat.id, "❌ Ви не авторизовані")
            return
        bot.send_message(message.chat.id, f"Вітаю, {message.from_user.full_name}", reply_markup=MAIN_MENU)

    @bot.message_handler(commands=["setconfig"], chat_types=["private"], func=lambda msg: msg.from_user.id in authorized_admins)
    def _set_config(message: Message):
        query = message.text.split(" ")
        if len(query) != 3:
            bot.send_message(message.chat.id, "❌ Помилка синтаксису")
            return
        if query[1] not in Config.get_instance().config:
            bot.send_message(message.chat.id, f"❌ Параметр {query[1]} не існує")
            return
        if query[1] in LOCKED_CONFIG_PARAMS:
            bot.send_message(message.chat.id, f"❌ Неможливо змінити параметр {query[1]}")
            return
        Config.get_instance().set(query[1], query[2])
        bot.send_message(message.chat.id, f"✅ <i>{query[1]}</i> = <i>{query[2]}</i>")

    @bot.message_handler(commands=["getconfig"], chat_types=["private"], func=lambda msg: msg.from_user.id in authorized_admins)
    def _get_config(message: Message):
        query = message.text.split(" ")
        if len(query) != 2:
            bot.send_message(message.chat.id, "❌ Помилка синтаксису")
            return
        if query[1] not in Config.get_instance().config:
            bot.send_message(message.chat.id, f"❌ Параметр {query[1]} не існує")
            return
        if query[1] in HIDDEN_CONFIG_PARAMS:
            bot.send_message(message.chat.id, f"❌ Неможливо отримати параметр {query[1]}")
            return
        bot.send_message(message.chat.id, f"ℹ️ <i>{query[1]}</i> = <i>{Config.get_instance().get(query[1])}</i>")

    @bot.message_handler(commands=["saveconfig"], chat_types=["private"], func=lambda msg: msg.from_user.id in authorized_admins)
    def _save_config(message: Message):
        Config.get_instance().save()
        bot.send_message(message.chat.id, f"✅ Конфігурацію збережено")

    @bot.message_handler(commands=["reloadconfig"], chat_types=["private"], func=lambda msg: msg.from_user.id in authorized_admins)
    def _reload_config(message: Message):
        Config.get_instance().reload()
        bot.send_message(message.chat.id, f"✅ Конфігурацію оновлено")

    @bot.message_handler(content_types=["text"], chat_types=["private"], func=lambda msg: msg.text == "📁 База товарів")
    def _products_database(message: Message):
        if message.from_user.id not in authorized_users:
            bot.send_message(message.chat.id, "❌ Ви не авторизовані")
            return
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📂 Відкрити базу", callback_data="create"))
        database_length = Product.select().count()
        bot.send_message(message.chat.id, f"▫️ Товарів в базі: {database_length}", reply_markup=markup)

    @bot.message_handler(content_types=["text"], chat_types=["private"],
                         func=lambda msg: msg.text == "📝 Генератор постів")
    def _post_generator_tip(message: Message):
        if message.from_user.id not in authorized_users:
            bot.send_message(message.chat.id, "❌ Ви не авторизовані")
            return
        bot.send_message(message.chat.id, "❕ Щоб створити пост відправте назву товару")

    @bot.message_handler(content_types=["text"], chat_types=["private"],
                         func=lambda msg: msg.text == Config.get_instance().get("password"))
    def _auth(message: Message):
        if message.from_user.id not in authorized_users:
            authorized_users.append(message.from_user.id)
            bot.send_message(message.chat.id, "✅ Успішна авторизація", reply_markup=MAIN_MENU)
        else:
            bot.send_message(message.chat.id, "❌ Ви вже авторизовані", reply_markup=MAIN_MENU)

    @bot.message_handler(content_types=["text"], chat_types=["private"],
                         func=lambda msg: msg.text == Config.get_instance().get("admin_password"))
    def _admin_auth(message: Message):
        if message.from_user.id not in authorized_admins:
            authorized_admins.append(message.from_user.id)
            bot.send_message(message.chat.id, "✅ Успішна авторизація адміністратора", reply_markup=MAIN_MENU)
        else:
            bot.send_message(message.chat.id, "❌ Ви вже авторизовані як адміністратор", reply_markup=MAIN_MENU)

    @bot.message_handler(content_types=["text"], chat_types=["private"])
    def _post_generator(message: Message):
        if message.from_user.id not in authorized_users:
            bot.send_message(message.chat.id, "❌ Ви не авторизовані")
            return
        bot.send_message(message.chat.id, generate_post(message.text), reply_markup=MAIN_MENU)

    @bot.callback_query_handler(func=lambda call: True)
    def _callback_handler(call: CallbackQuery):
        if call.from_user.id not in authorized_users:
            bot.send_message(call.message.chat.id, "❌ Ви не авторизовані")
            bot.answer_callback_query(call.id)
            return
        query = call.data.split(" ")
        if query[0] == "create":
            try:
                product = Product.get(Product.id == 1)
                markup = generate_iterator_keyboard(product.id)
                with open(product.image, "rb") as image:
                    bot.send_message(call.message.chat.id, "❕ Ви відкрили базу товарів", reply_markup=ReplyKeyboardRemove())
                    bot.delete_message(call.message.chat.id, call.message.id)
                    bot.send_photo(call.message.chat.id, image, caption=f"<b>ID #{product.id}</b>\n{product.name}\nЦіна: {product.price} грн", reply_markup=markup)
                bot.answer_callback_query(call.id)
            except DoesNotExist:
                bot.answer_callback_query(call.id, "❌ Виникла помилка", show_alert=True)
        elif query[0] == "show":
            try:
                product = Product.get(Product.id == int(query[1]))
                markup = generate_iterator_keyboard(product.id)
                with open(product.image, "rb") as image:
                    bot.delete_message(call.message.chat.id, call.message.id)
                    bot.send_photo(call.message.chat.id, image, caption=f"<b>ID #{product.id}</b>\n{product.name}\nЦіна: {product.price} грн", reply_markup=markup)
                bot.answer_callback_query(call.id)
            except DoesNotExist:
                bot.answer_callback_query(call.id, "❌ Товар з таким ID відсутній", show_alert=True)
        elif query[0] == "close":
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, "❕ Ви закрили базу товарів", reply_markup=MAIN_MENU)
            bot.answer_callback_query(call.id)

    bot.polling()


if __name__ == "__main__":
    main()
