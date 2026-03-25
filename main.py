import threading
import datetime
import telebot
from telebot import types
import Config

import time
bot = telebot.TeleBot(Config.api_key)
album_storage ={}
storagePhoto = []
userMode={}
Group_ID = Config.groups_id
temp_data ={}
def Delivery_shape():

    while True:
        current_time = datetime.datetime.now().strftime("%H:%M")

        to_send = [item for item in storagePhoto if item["send_time"] == current_time]

        if to_send:
                try:
                    media=[]
                    for i, item in enumerate(to_send):
                        caption = item.get('caption') if i == 0 else None
                        media.append(types.InputMediaPhoto(item['file_id'], caption=caption))
                    bot.send_media_group(to_send[0]['chat_id'], media)
                    for item in to_send:
                        storagePhoto.remove(item)
                        print(f"{current_time}, Альбом отправлен!")

                except Exception as e:
                    print(e)
        time.sleep(2)

threading.Thread(target=Delivery_shape, daemon=True).start()


@bot.message_handler(commands =['start'])
def sendMessage(message):
    try:
        bot.send_message(message.chat.id, "Привет, я ботик❤️ и всё что я умею делать это отправлять фотки для вашей группы в определённое время. К примеру вы можете желать подписчикам спокойной ночи и доброе утро. Если что-то не то выложили, то можете удалить все фотографии ")
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Выбрать фотографии для доброе утро и спокойной ночи', callback_data='mode:photo'))
        keyboard.add(types.InlineKeyboardButton(text='Выбрать Очистеть всё!!!', callback_data='mode:Clear'))
        bot.send_message(message.chat.id,"Выберите режим", reply_markup=keyboard)
    except Exception as e:
        print(e)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('set_h:', 'set_m:')))
def handle_time_selection(call):
    try:
        user_id = call.message.chat.id
        data = call.data.split(':')
        action = data[0]
        value = data[1]
        if user_id not in temp_data:
            temp_data[user_id] = {}
        if action == 'set_h':
            temp_data[user_id]['hour'] = value.zfill(2)
            markup = types.InlineKeyboardMarkup(row_width=6)
            minutes = ["00","10","20","30","40","50"]
            buttons = [types.InlineKeyboardButton(m, callback_data=f"set_m:{m}") for m in minutes]
            markup.add(*buttons)
            bot.edit_message_text(f"Выбран час:{value}.теперь выберите минуты", chat_id=user_id, message_id=call.message.message_id, reply_markup=markup)
        elif action =='set_m':
            hour = temp_data[user_id]['hour']
            minute = value.zfill(2)
            full_time = f"{hour}:{minute}"
            temp_data[user_id]['time'] =full_time
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text='не делать подпись', callback_data='caption:none'))

            bot.edit_message_text(f"Время установлено: {full_time} Введите подпись для фото(или нажмите нет):", chat_id=user_id, message_id= call.message.message_id, reply_markup=keyboard)


            bot.register_next_step_handler(call.message, get_caption, user_id)
    except Exception as e:
        print(e)
@bot.callback_query_handler(func = lambda call: call.data.startswith('mode:'))
def set_quest(call):
    try:
        mode = call.data.split(':')[1]
        user_id= call.message.chat.id
        userMode[user_id] = mode

        if mode == 'photo':
            bot.send_message(call.message.chat.id, "режим отправки фото. Отправьте фото или несколько фотографий")
        elif mode == 'Clear':
            storagePhoto.clear()
            album_storage.clear()
            temp_data.clear()
            bot.send_message(call.message.chat.id, "Всё очищено. Выберите /start для начала")
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.send_message(call.message.chat.id, " Выберите режим")


@bot.message_handler(content_types=['photo'])
def set_morning(message):
    try:
        user_id = message.chat.id
        if userMode.get(user_id) != 'photo':
            bot.send_message(user_id, "Сначала выберите режим в /start")
            return
        file_id = message.photo[-1].file_id
        if message.media_group_id is None:

            process_album_done(message,[file_id])
            return
        if message.media_group_id not in album_storage:
            album_storage[message.media_group_id] = []
            threading.Timer(1.5, process_album_done, args=[message, album_storage[message.media_group_id], message.media_group_id]).start()
    except Exception as e:
        print(e)
    album_storage[message.media_group_id].append(message.photo[-1].file_id)
def process_album_done(message, file_ids, group_id=None):
    try:
        user_id = message.chat.id
        if group_id and group_id in album_storage:
            del album_storage[group_id]
        temp_data[user_id] = {'file_ids': file_ids}
        markup = types.InlineKeyboardMarkup(row_width=6)
        buttons = [types.InlineKeyboardButton(str(h).zfill(2), callback_data=f"set_h:{h}") for h in range(24)]
        markup.add(*buttons)
        bot.send_message(user_id, "Фото получено! Выберите час для отправки ", reply_markup=markup)
    except Exception as e:
        print(e)

def process_time_step(message, file_id):
    try:
        scheduled_time = message.text
        if ":" not in scheduled_time:
            bot.send_message(message.chat.id,"Ошибка формата")
            return

        msg = bot.send_message(message.chat_id, "Введите текст для подписи")
        bot.register_next_step_handler(msg, get_caption, file_id, scheduled_time)
    except Exception as e:
        print(e)
@bot.callback_query_handler(func=lambda call: call.data =='caption:none')
def cancel_caption_callback(call):
    try:
        user_id = call.message.chat.id
        bot.clear_step_handler_by_chat_id(chat_id=user_id)

        save_photos_to_storage(user_id, caption=None)
        bot.edit_message_text("сохранено без подписи", chat_id=user_id, message_id=call.message.message_id)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(e)
def save_photos_to_storage(user_id, caption):
    try:
        data = temp_data.get(user_id)
        if data and 'file_ids' in data and 'time' in data:
            for f_id in data['file_ids']:
                storagePhoto.append({
                    "chat_id": Group_ID,
                    "file_id": f_id,
                    "send_time": data["time"],
                    "caption": caption,

                })

            if user_id in temp_data:
                del temp_data[user_id]
    except Exception as e:
        print(e)
def get_caption(message, user_id ):
    try:
        caption = message.text

        data =temp_data.get(user_id)
        time_str = data['time']
        save_photos_to_storage(user_id, caption)

        bot.send_message(user_id, f"Готово! фотки запланированы на{time_str}")
    except Exception as e:
        print(e)

bot.infinity_polling()
