import telebot
from telebot import types
import Config
import uuid
import schedule
import time
bot = telebot.TeleBot(Config.api_key)

ContainerMorning = {}
ContainerNight = {}
userMode ={}
ContainerUrl ={}
TempPhoto ={}
sendTime = {
    "Morning": None,
    "Night": None
}
@bot.message_handler(command =["start"])
def sendMessage(message):


    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Выбрать фотографии для доброе утро', callback_data='mode:Morning'))
    keyboard.add(types.InlineKeyboardButton(text='Выбрать фотографии для доброе утро', callback_data='mode:Night'))
    keyboard.add(types.InlineKeyboardButton(text='Выбрать Очистеть всё!!!', callback_data='mode:Clear'))
    bot.send_message(message.chat.id,"Выберите режим", reply_markup=keyboard)



@bot.callback_query_handler(func = lambda call: call.data.startswith('mode:'))
def set_quest(call):
    try:
        mode = call.data.split(':')[1]
        user_id= call.message.chat.id
        userMode[user_id] = mode

        if mode == 'Morning':
            bot.send_message(call.message.chat.id, "режим доброе утро")
            return

        elif mode == 'Night':
            bot.send_message(call.message.chat.id, "режим спокойной ночи")
            return
        elif mode == 'Clear':
            ContainerMorning.clear()
            ContainerNight.clear()
            sendTime["Morning"] = None
            sendTime["Night"] = None
            TempPhoto.clear()
            bot.send_message(call.message.chat.id, "Всё очищено. Выберите /start для начала")
            return
    except:
        bot.send_message(call.message.chat.id, " Выберите режим")

@bot.message_handler(content_types=['Clear'])
def ClearContainer(message):
    ContainerMorning.clear()
    ContainerNight.clear()
    sendTime.clear()
    TempPhoto.clear()
    bot.send_message(message.chat.id,"Очистел всё. Выберите /start для начало")
@bot.message_handler(content_types=['Morning'])
def set_morning(message):
    user_id =message.chat.id
    if not  message.chat.id:
        bot.send_message(user_id, "")
        return
    bot.send_message(message.chat.id,"Вы выбрали режим доброе утро. Отправьте мне фотографии и я распределю их по порядку и буду отправлять в определённое время")

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image_id =str(uuid.uuid4())
    ContainerMorning[image_id] = downloaded_file
    keyboard = types.InlineKeyboardMarkup()

    bot.send_message(message.chat.id,"хотите добавить подпись для этой картинки?")
    keyboard.add(types.InlineKeyboardButton(text='да', callback_data="mode:yes"))

    keyboard.add(types.InlineKeyboardButton(text='нет', callback_data="mode:no"))



@bot.message_handler(content_types=['Night'])
def set_night(message):
    bot.send_message(message.chat.id,"Вы выбрали режим спокойной ночи. Отправьте мне фотографии и я распределю их по порядку и буду отправлять в определённое время")


