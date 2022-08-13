import json
import os.path
from io import BytesIO

import requests
from peewee import DoesNotExist
from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove

from models import Product

DEFAULT_CONFIG = {
    "bot_token": "change_this_bot_token",
    "password": "change_this_password",
    "admin_password": "change_this_admin_password"
}

LOCKED_CONFIG_PARAMS = [
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

    if os.path.exists("config.json"):
        with open("config.json") as config_file:
            config = json.load(config_file)
    else:
        with open("config.json", "w") as config_file:
            json.dump(DEFAULT_CONFIG, config_file, indent=2)
        print("Config file does not exist, default config will be created")
        print("Set the bot token and passwords in the config, then run the bot")
        exit(0)

    authorized_users = []
    authorized_admins = []

    bot = TeleBot(config["bot_token"], parse_mode="HTML")

    @bot.message_handler(commands=["start"], chat_types=["private"])
    def _start(message: Message):
        if message.from_user.id not in authorized_users:
            bot.send_message(message.chat.id, "❌ Ви не авторизовані")
            return
        bot.send_message(message.chat.id, f"Вітаю, {message.from_user.full_name}", reply_markup=MAIN_MENU)

    @bot.message_handler(commands=["set"], chat_types=["private"], func=lambda msg: msg.from_user.id in authorized_admins)
    def _set(message: Message):
        query = message.text.split(" ")
        if len(query) != 3:
            bot.send_message(message.chat.id, "❌ Помилка синтаксису")
            return
        if query[1] not in config:
            bot.send_message(message.chat.id, f"❌ Параметр {query[1]} не існує")
            return
        if query[1] in LOCKED_CONFIG_PARAMS:
            bot.send_message(message.chat.id, f"❌ Неможливо змінити параметр {query[1]}")
            return
        config[query[1]] = query[2]
        bot.send_message(message.chat.id, f"✅ {query[1]}={query[2]}")

    @bot.message_handler(commands=["saveconfig"], chat_types=["private"], func=lambda msg: msg.from_user.id in authorized_admins)
    def _save_config(message: Message):
        with open("config.json", "w") as _config_file:
            json.dump(config, _config_file, indent=2)
        bot.send_message(message.chat.id, f"✅ Конфігурацію збережено")

    @bot.message_handler(content_types=["text"], chat_types=["private"], func=lambda msg: msg.text == "📁 База товарів")
    def _products_database(message: Message):
        if message.from_user.id not in authorized_users:
            bot.send_message(message.chat.id, "❌ Ви не авторизовані")
            return
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📂 Відкрити базу", callback_data="create"))
        database_length = Product.select().count()
        bot.send_message(message.chat.id, f"▫️ Товарів в базі: {database_length}", reply_markup=markup)

    @bot.message_handler(content_types=["text"], chat_types=["private"], func=lambda msg: msg.text == "📝 Генератор постів")
    def _post_generator_tip(message: Message):
        if message.from_user.id not in authorized_users:
            bot.send_message(message.chat.id, "❌ Ви не авторизовані")
            return
        bot.send_message(message.chat.id, "❕ Щоб створити пост відправте назву товару")

    @bot.message_handler(content_types=["text"], chat_types=["private"],
                         func=lambda msg: msg.text == config["password"])
    def _auth(message: Message):
        if message.from_user.id not in authorized_users:
            authorized_users.append(message.from_user.id)
            bot.send_message(message.chat.id, "✅ Успішна авторизація", reply_markup=MAIN_MENU)
        else:
            bot.send_message(message.chat.id, "❌ Ви вже авторизовані", reply_markup=MAIN_MENU)

    @bot.message_handler(content_types=["text"], chat_types=["private"],
                         func=lambda msg: msg.text == config["admin_password"])
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
                image = BytesIO(requests.get(product.image).content)
                image.seek(0)
                bot.delete_message(call.message.chat.id, call.message.id)
                bot.send_message(call.message.chat.id, "❕ Ви відкрили базу товарів", reply_markup=ReplyKeyboardRemove())
                bot.send_photo(call.message.chat.id, image,
                               caption=f"<b>ID #{product.id}</b>\n{product.name}\nЦіна: {product.price} грн",
                               reply_markup=markup)
                bot.answer_callback_query(call.id)
            except DoesNotExist:
                bot.answer_callback_query(call.id, "❌ Виникла помилка", show_alert=True)
        elif query[0] == "show":
            try:
                product = Product.get(Product.id == int(query[1]))
                markup = generate_iterator_keyboard(product.id)
                image = BytesIO(requests.get(product.image).content)
                image.seek(0)
                bot.delete_message(call.message.chat.id, call.message.id)
                bot.send_photo(call.message.chat.id, image,
                               caption=f"<b>ID #{product.id}</b>\n{product.name}\nЦіна: {product.price} грн",
                               reply_markup=markup)
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
