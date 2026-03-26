import threading
import datetime
import telebot

from telebot import types
import Config
import pytz
import time
import json
import os
SETTINGS_FILE = 'user_settings.json'

bot = telebot.TeleBot(Config.api_key)
album_storage ={}
storagePhoto = []
userMode={}


temp_data ={}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_settings(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

user_setting = load_settings()

@bot.message_handler(commands =['start'])
def sendMessage(message):
    try:
        bot.send_message(message.chat.id, "Привет, я ботик❤️ и всё что я умею делать это отправлять фотки для вашей группы в определённое время.\n К примеру вы можете желать подписчикам спокойной ночи и доброе утро.\n Если что-то не то выложили, то можете удалить все фотографии ")
        msg =bot.send_message(message.chat.id,"Для начало работы вам необходим токен от группы. Чтобы получить токен небходимо в свою группу добавить @Getmyid_Work_Bot(Он выдаст вам токен. Пример'-1992002323210')\n И для работы ещё необходимо добавить меня в группу для отправки фоток ")
        bot.register_next_step_handler(msg, SetTokenGroup)


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
        album_storage[message.media_group_id].append(message.photo[-1].file_id)
    except Exception as e:
        print(e)

def process_album_done(message, file_ids, group_id=None):
    try:
        user_id = message.chat.id
        if group_id and group_id in album_storage:
            del album_storage[group_id]
        temp_data[user_id] = {'file_ids': file_ids}

        msg =bot.send_message(user_id, "Фото получено! Выберите время для отправки в формате ЧЧ:MM (Например, 07:00 или 22:00) ")
        bot.register_next_step_handler(msg, process_time_step, user_id)
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
        uid_str = str(user_id)
        if data and 'file_ids' in data and 'time' in data:
            target_group = user_setting[uid_str].get('group_id')
            for f_id in data['file_ids']:
                storagePhoto.append({
                    "user_id": user_id,
                    "chat_id": target_group,
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


def Delivery_shape():
    while True:

        for user_id_str, config in user_setting.items():
            try:

                user_tz = pytz.timezone(config.get('timezone', 'UTC'))
                current_time = datetime.datetime.now(user_tz).strftime("%H:%M")


                to_send = [item for item in storagePhoto if
                           item["send_time"] == current_time and str(item["user_id"]) == user_id_str]

                if to_send:
                    media = []
                    for i, photo_item in enumerate(to_send):

                        caption = photo_item.get('caption') if i == 0 else None
                        media.append(types.InputMediaPhoto(photo_item['file_id'], caption=caption))


                    target_chat = config.get('group_id')

                    if target_chat:
                        bot.send_media_group(target_chat, media)


                        for sent_item in to_send:
                            if sent_item in storagePhoto:
                                storagePhoto.remove(sent_item)

                        print(f"[{current_time}] Альбом отправлен для {user_id_str} в группу {target_chat}")
                    else:
                        print(f"Ошибка: У юзера {user_id_str} не настроен group_id")

            except Exception as e:
                print(f"Ошибка планировщика для {user_id_str}: {e}")


        time.sleep(30)


threading.Thread(target=Delivery_shape, daemon=True).start()
def process_time_step(message, user_id):
    try:
        scheduled_time = message.text.strip()
        if len(scheduled_time) != 5 or ":" not in scheduled_time:
            bot.send_message(message.chat.id,"Неверный формат! Пожалуйста, введите время ровно в формате ЧЧ:MM (Например, 07:00 или 22:00) ")
            return
        try:
            datetime.datetime.strptime(scheduled_time, "%H:%M")
        except ValueError:
            msg = bot.send_message(user_id,  "Такого времени не существует! Часы должны быть от 00 до 23, а минуты от 00 до 59.\nПопробуйте еще раз:")
            bot.register_next_step_handler(msg, process_time_step, user_id)
            return
        if user_id not in temp_data:
            temp_data[user_id] ={}
        temp_data[user_id]['time'] = scheduled_time

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Не делать подпись", callback_data='caption:none'))

        msg = bot.send_message(message.chat.id, f"Время установлено: {scheduled_time}\n Введите подпись (Или не добавлять подпись)", reply_markup=keyboard)
        bot.register_next_step_handler(msg, get_caption, user_id)
    except Exception as e:
        print(e)
def SetTokenGroup(message):
    try:
        user_id = str(message.chat.id)
       
        token = message.text.strip()
        if not token.replace('-', '', 1).isdigit():
            msg = bot.send_message(message.chat.id, "❌ В ID группы должны быть только цифры (и минус в начале)! Попробуйте еще раз:")
            bot.register_next_step_handler(msg, SetTokenGroup)
            return
        if user_id not in user_setting:
            user_setting[user_id] = {}
        user_setting[user_id]['group_id'] = token
        save_settings(user_setting)
        msg = bot.send_message(message.chat.id, "Токен сохранён! теперь введите ваш часовой пояс. На сайте https://www.zeitverschiebung.net/ можете найти свой часовой пояс.  Пример: Asia/Irkutsk")
        bot.register_next_step_handler(msg, SetTimeZone)
    except Exception as e:
        msg = bot.send_message(message.chat.id, f"❌ Ошибка в токена. Попробуйте ввести еще раз:{e}")

        bot.register_next_step_handler(msg, SetTokenGroup)
def SetTimeZone(message):
    try:
        user_id = str(message.chat.id)
        zone_name = message.text.strip()

        pytz.timezone(zone_name)
        if user_id not in user_setting:
            user_setting[user_id] = {}

        user_setting[user_id]['timezone'] = zone_name
        save_settings(user_setting)
        keyboard = types.InlineKeyboardMarkup()

        bot.send_message(message.chat.id, f"Настройка завершена! \n {user_setting[user_id]['group_id']} \n Пояс: {zone_name}")
        keyboard.add(types.InlineKeyboardButton(text='Выбрать: фотографии для доброе утро и спокойной ночи',
                                                callback_data='mode:photo'))
        keyboard.add(types.InlineKeyboardButton(text='Выбрать: удалить!!!', callback_data='mode:Clear'))
        bot.send_message(message.chat.id, "Выберите режим", reply_markup=keyboard)
    except Exception:
        msg = bot.send_message(message.chat.id, "❌ Ошибка в названии пояса. Попробуйте ввести еще раз:")

        bot.register_next_step_handler(msg, SetTimeZone)

bot.infinity_polling()
