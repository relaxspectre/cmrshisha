from telegram import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo



def worker_menu():
    keyboard = [
        [KeyboardButton("Почати зміну"), KeyboardButton("Закрити зміну")],
        [KeyboardButton("Додати продаж"), KeyboardButton("Списання табаку")],
        [KeyboardButton("Мої виплати")],
        [KeyboardButton("📊 Відкрити панель", web_app=WebAppInfo(url="https://chicanesrt.shop"))],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def owner_menu():
    keyboard = [
        [KeyboardButton("Дашборд"), KeyboardButton("Каса")],
        [KeyboardButton("Статистика"), KeyboardButton("Працівники")],
        [KeyboardButton("Склад"), KeyboardButton("Виплати")],
        [KeyboardButton("Внести витрату"), KeyboardButton("Внести виплату")],
        [KeyboardButton("Додати прихід")],
        [KeyboardButton("📊 Відкрити панель", web_app=WebAppInfo(url="https://chicanesrt.shop"))],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)