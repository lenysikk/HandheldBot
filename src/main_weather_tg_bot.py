import asyncio
import re
import wikipedia

import requests
import datetime

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from bs4 import BeautifulSoup
from googletrans import Translator

from db import Database

from config import tg_bot_token, open_weather_token
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor

bot = Bot(token=tg_bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())
db = Database("bot_database.db")
wikipedia.set_lang('ru')
alphabet = ' 1234567890-йцукенгшщзхъфывапролджэячсмитьбюёqwertyuiopasdfghjklzxcvbnm?%.,()!:;'
url = 'https://horo.mail.ru/prediction/'
translator = Translator()

class Zodiac():
    code_to_zodiac = {
        "Телец \U00002649": "taurus",
        "Рак \U0000264B": "cancer",
        "Стрелец \U00002650": "sagittarius",
        "Козерог \U00002651": "capricorn",
        "Скорпион \U0000264F": "scorpio",
        "Водолей \U00002652": "aquarius",
        "Рыбы \U00002653": "pisces",
        "Дева \U0000264D": "virgo",
        "Овен \U00002648": "aries",
        "Лев \U0000264C": "leo",
        "Весы \U0000264E": "libra",
        "Близнецы \U0000264A": "gemini"
    }

class Form(StatesGroup):
    weather_state = State()
    remind_state = State()
    minutes_state = State()
    base_state = State()
    note_state = State()
    create_note = State()
    wiki_state = State()
    horoscope_state = State()
    horoscope_result_state = State()

def horoscope_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_today = types.KeyboardButton('Сегодня \U0001F51B')
    button_tomorrow = types.KeyboardButton('Завтра \U0001F51C')
    button_week = types.KeyboardButton('Неделя \U0001F4C5')
    return markup.add(button_today, button_tomorrow, button_week)

def yes_or_no_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_yes = types.KeyboardButton('Да \U00002705')
    button_no = types.KeyboardButton('Нет \U0000274C')
    return markup.add(button_yes, button_no)

def horoscope_zodiac_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_taurus = types.KeyboardButton('Телец \U00002649')
    button_cancer = types.KeyboardButton('Рак \U0000264B')
    button_sagittarius = types.KeyboardButton('Стрелец \U00002650')
    button_capricorn = types.KeyboardButton('Козерог \U00002651')
    button_scorpio = types.KeyboardButton('Скорпион \U0000264F')
    button_aquarius = types.KeyboardButton('Водолей \U00002652')
    button_pisces = types.KeyboardButton('Рыбы \U00002653')
    button_virgo = types.KeyboardButton('Дева \U0000264D')
    button_aries = types.KeyboardButton('Овен \U00002648')
    button_leo = types.KeyboardButton('Лев \U0000264C')
    button_libra = types.KeyboardButton('Весы \U0000264E')
    button_gemini = types.KeyboardButton('Близнецы \U0000264A')

    return markup.add(button_gemini, button_libra, button_aries, button_virgo, button_leo, button_pisces, button_aquarius, button_scorpio, button_capricorn, button_sagittarius, button_taurus, button_cancer)

def standart_markup(id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_weather = types.KeyboardButton('Погода \U0001F324')
    button_reminder = types.KeyboardButton('Напомнить \U000023F0')
    button_note = types.KeyboardButton('Заметки \U0001F4DD')
    button_wiki = types.KeyboardButton('Найти в Википедии \U0001F50E')
    button_horoscope = types.KeyboardButton('Получить гороскоп \U0001F30C')
    if id == 786869478:
        button_emergency = types.KeyboardButton('Разослать напоминания \U000026A0')
        markup.add(button_emergency)
    return markup.add(button_weather, button_reminder, button_note, button_wiki, button_horoscope)

def clean_str(r):
    r = r.lower()
    r = [c for c in r if c in alphabet]
    return ''.join(r)

def get_wiki(s):
    try:
        ny = wikipedia.page(s)
        wikitext=ny.content[:1000]
        wikimas=wikitext.split('.')
        wikimas = wikimas[:-1]
        wikitext2 = ''
        for x in wikimas:
            if not('==' in x):
                if(len((x.strip()))>3):
                    wikitext2=wikitext2+x+'.'
            else:
                break
        wikitext2=re.sub('\([^()]*\)', '', wikitext2)
        wikitext2=re.sub('\([^()]*\)', '', wikitext2)
        wikitext2=re.sub('\{[^\{\}]*\}', '', wikitext2)
        return wikitext2
    except Exception as e:
        return 'В Википедии нет информации об этом'

def get_horoscope(url):
    try:
        response = requests.get(url).text
        soup = BeautifulSoup(response, 'lxml')
        block = soup.find('div', {"class": "layout"})
        block = block.find('div', {"class": "article__text"}).text
        return block
    except:
        print("GET запрос не выполнен")
        return 'Прости,какая-то ошибка.\nТебя точно ждёт чудесный день!'

@dp.message_handler(commands=["start"], state=None)
async def start_command(message: types.Message) -> None:
    markup = standart_markup(message.from_user.id)
    if message.chat.type == 'private':
        if not db.user_exists(message.from_user.id):
            db.add_user(message.from_user.id)

    await message.reply("Привет! Выбери действие\n", reply_markup=markup)
    await Form.base_state.set()


@dp.message_handler(state=Form.base_state)
async def bot_message(message: types.Message, state: FSMContext) -> None:
    global translator
    if message.text == 'Погода \U0001F324':
        await message.reply("Введи название города:")
        await Form.weather_state.set()
    elif message.text == 'Получить гороскоп \U0001F30C':
        try:
            zodiac = await db.get_zodiac_by_id(message.from_user.id)
        except:
            print('Ошибка получения данных из базы')
        if zodiac != None:
            if zodiac == 'leo':
                zodiac = 'Lev'
            zodiac = translator.translate(zodiac, dest='ru').text
            markup = yes_or_no_markup()
            await bot.send_message(message.chat.id, "Ваш знак зодиака - " + zodiac + "?", reply_markup=markup)
            await Form.horoscope_state.set()
        else:
            markup = horoscope_zodiac_markup()
            await message.reply("Выберите свой знак зодиака", reply_markup=markup)
            await Form.horoscope_state.set()
    elif message.text == 'Напомнить \U000023F0':
        await message.reply("Что тебе напомнить и во сколько?\nВведи сначала время в формате - ЧЧ:ММ, а потом текст\nНапример:  18:30 покормить кота")
        await Form.remind_state.set()
    elif message.text == 'Разослать напоминания \U000026A0':
        task_emergency = asyncio.create_task(remind_all_emergency())
        await task_emergency
    elif message.text == 'Найти в Википедии \U0001F50E':
        await message.reply("Введи слово:")
        await Form.wiki_state.set()
    elif message.text == 'Заметки \U0001F4DD':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_create = types.KeyboardButton('Создать заметку')
        button_get = types.KeyboardButton('Получить заметку \U00002705')
        markup.add(button_create, button_get)
        await message.reply("Выбери действие", reply_markup=markup)
        await Form.note_state.set()

async def remind_all_emergency() -> None:
    users = await db.get_users()
    for user in users:
        if (user[2] != None):
            await bot.send_message(user[1], "Напоминаю взаранее: " + user[2] + "\nиз-за технической неполадки\nЕсли ещё нуждаетесь в напоминании, пересоздайте напоминание и точно ничего не забудете\nС любовью, команда Handheld Remind Bot!) \U0001F468")
            await db.delete_remind(user[1])

@dp.message_handler()
async def bot_message(message: types.Message, state: FSMContext) -> None:
    global translator
    if message.text == 'Погода \U0001F324':
        await message.reply("Введи название города:")
        await Form.weather_state.set()
    elif message.text == 'Получить гороскоп \U0001F30C':
        try:
            zodiac = await db.get_zodiac_by_id(message.from_user.id)
        except:
            print('Ошибка получения данных из базы')
        if zodiac != None:
            markup = yes_or_no_markup()
            if zodiac == 'leo':
                zodiac = 'Lev'
            print(zodiac)
            zodiac = translator.translate(zodiac, dest='ru').text
            print(zodiac)
            await bot.send_message(message.chat.id, "Ваш знак зодиака - " + zodiac + "?", reply_markup=markup)
            await Form.horoscope_state.set()
        else:
            markup = horoscope_zodiac_markup()
            await message.reply("Выберите свой знак зодиака", reply_markup=markup)
            await Form.horoscope_state.set()
    elif message.text == 'Напомнить \U000023F0':
        await message.reply("Что тебе напомнить и во сколько?\nВведи сначала время в формате - ЧЧ:ММ, а потом текст\nНапример:  18:30 покормить кота")
        await Form.remind_state.set()
    elif message.text == 'Найти в Википедии \U0001F50E':
        await message.reply("Введи слово:")
        await Form.wiki_state.set()
    elif message.text == 'Заметки \U0001F4DD':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_create = types.KeyboardButton('Создать заметку')
        button_get = types.KeyboardButton('Получить заметку \U00002705')
        markup.add(button_create, button_get)
        await message.reply("Выбери действие", reply_markup=markup)
        await Form.note_state.set()

@dp.message_handler(state=Form.wiki_state)
async def note_operation(message: types.Message, state= FSMContext) -> None:
    await message.reply(get_wiki(message.text))
    markup = standart_markup(message.from_user.id)
    await message.reply("Выбери действие\n", reply_markup=markup)
    await Form.base_state.set()

@dp.message_handler(state=Form.horoscope_state)
async def note_operation(message: types.Message, state= FSMContext) -> None:
    global url
    text = message.text
    if text == 'Да \U00002705':
        try:
            result = await db.get_zodiac_by_id(message.from_user.id)
        except:
            print("Ошибка работы базы данных")
        url += result
        url += '/'
        await Form.horoscope_result_state.set()
    elif text == 'Нет \U0000274C':
        await db.delete_zodiac(message.from_user.id)
        markup = horoscope_zodiac_markup()
        await message.reply("Выберите свой знак зодиака", reply_markup=markup)
        await Form.horoscope_state.set()
        return
    elif text in Zodiac.code_to_zodiac:
        result = Zodiac.code_to_zodiac[text]
        url += result
        url +='/'
        await db.set_zodiac(message.from_user.id, result)

    markup = horoscope_markup()
    await message.reply("Выберите период на который хотите получить гороскоп", reply_markup=markup)
    await Form.horoscope_result_state.set()

@dp.message_handler(state=Form.horoscope_result_state)
async def note_operation(message: types.Message, state= FSMContext) -> None:
    global url
    text = message.text
    if text == 'Сегодня \U0001F51B':
        url += 'today/'
    elif text == 'Завтра \U0001F51C':
        url += 'tomorrow/'
    elif text == 'Неделя \U0001F4C5':
        url += 'week/'

    await bot.send_message(message.chat.id, "Ваш гороскоп:\n" + get_horoscope(url))

    url = 'https://horo.mail.ru/prediction/'
    markup = standart_markup(message.from_user.id)
    await bot.send_message(message.chat.id, "Выберите дальнейшее действие", reply_markup=markup)
    await Form.base_state.set()

@dp.message_handler(state=Form.note_state)
async def note_operation(message: types.Message, state= FSMContext) -> None:
    if message.text == 'Создать заметку':
        await bot.send_message(message.chat.id, "Введите текст заметки:")
        await Form.create_note.set()
    if message.text == 'Получить заметку \U00002705':
        try:
            users = await db.get_info_by_id(message.from_user.id)
            await message.reply(users[0][4])
        except:
            print("Ошибка работы с базой данных")
            await message.reply('Заметок нет')

        markup = standart_markup(message.from_user.id)
        await message.reply("Выбери действие\n", reply_markup=markup)
        await Form.base_state.set()

@dp.message_handler(state=Form.create_note)
async def create_note(message: types.Message, state= FSMContext) -> None:
    try:
        await db.create_note(message.from_user.id, message.text)
        await bot.send_message(message.from_user.id, "Заметка успешно создана!")
    except:
        print('Ошибка работы с базой данных')
        await bot.send_message(message.from_user.id, "Заметка не создана, попробуйте позднее!")

    markup = standart_markup(message.from_user.id)
    await message.reply("Выбери действие\n", reply_markup=markup)
    await Form.base_state.set()

@dp.message_handler(state=Form.weather_state)
async def get_weather(message: types.Message, state= FSMContext) -> None:
    code_to_smile = {
        "Clear": "Ясно \U00002600",
        "Clouds": "Облачно \U00002601",
        "Rain": "Дождь \U00002614",
        "Drizzle": "Дождь \U00002614",
        "Thunderstorm": "Гроза \U000026A1",
        "Snow": "Снег \U0001F328",
        "Mist": "Туман \U0001F32B"
    }

    try:
        r = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={open_weather_token}&units=metric"
        )
        data = r.json()
        city = data["name"]
        cur_weather = int(data["main"]["temp"])

        weather_description = data["weather"][0]["main"]
        if weather_description in code_to_smile:
            wd = code_to_smile[weather_description]
        else:
            wd = "Посмотри в окно, не пойму что там за погода!"

        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind = data["wind"]["speed"]
        sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
        sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])
        length_of_the_day = datetime.datetime.fromtimestamp(data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(
            data["sys"]["sunrise"])
        clothes = ""
        wind_ten = 1.5 * wind
        twc = 13.12 + 0.6215*cur_weather - 11.37* wind**0.16 + 0.3965 * cur_weather* wind_ten**0.16
        if twc < -5 and twc > -20:
            clothes +="Надень пуховик и теплую кофту \U0001F9E4"
        elif twc <= -20:
            clothes +="Надень теплую зимнюю куртку и не забудь шарф \U0001F9E4"
        elif twc >= -5 and twc < 0:
            clothes +="Сегодня надень свитшот и весенную куртку \U0001F9E5"
        elif twc >= 0 and twc < 10:
            clothes +="Сегодня стоит надень весенную куртку и толстовку с капюшоном \U0001F456"
        elif twc >= 10 and twc < 15:
            clothes +="Сегодня можно надеть лёгкую ветровку \U0001F45F"
        elif twc >= 15:
            clothes +="Можешь смело надевать футболку и шорты \U0001F455 \U0001FA73"

        if wd == "Ясно \U00002600" and twc > 10:
            clothes +=",\nне забудь взять кепку) \U0001F9E2"
        elif (wd == "Дождь \U00002614" or wd == "Дождь \U00002614" or wd == "Гроза \U000026A1" ) and twc > 0:
            clothes +=",\nне забудь взять зонтик) \U00002602"

        await message.reply(f"Сегодня: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                            f"Погода в городе: {city}\nТемпература: {cur_weather}C° {wd}\n"
                            f"Влажность: {humidity}%\nДавление: {pressure} мм.рт.ст\nВетер: {wind} м/с\n"
                            )
        await bot.send_message(message.chat.id, f"{clothes}\n"f"Удачного тебе дня!")

        markup = standart_markup(message.from_user.id)

        await bot.send_message(message.chat.id, "Выбери дальнейшее действие", reply_markup=markup)
        await Form.base_state.set()
    except:
        await message.reply("\U0001F914 Проверьте название города и введите заново\U0001F504")
        await Form.weather_state.set()

@dp.message_handler(state=Form.weather_state)
async def get_weather(message: types.Message, state= FSMContext) -> None:
    code_to_smile = {
        "Clear": "Ясно \U00002600",
        "Clouds": "Облачно \U00002601",
        "Rain": "Дождь \U00002614",
        "Drizzle": "Дождь \U00002614",
        "Thunderstorm": "Гроза \U000026A1",
        "Snow": "Снег \U0001F328",
        "Mist": "Туман \U0001F32B"
    }

    try:
        r = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={open_weather_token}&units=metric"
        )
        data = r.json()
        city = data["name"]
        cur_weather = int(data["main"]["temp"])

        weather_description = data["weather"][0]["main"]
        if weather_description in code_to_smile:
            wd = code_to_smile[weather_description]
        else:
            wd = "Посмотри в окно, не пойму что там за погода!"

        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind = data["wind"]["speed"]
        sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
        sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])
        length_of_the_day = datetime.datetime.fromtimestamp(data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(
            data["sys"]["sunrise"])
        clothes = ""
        wind_ten = 1.5 * wind
        twc = 13.12 + 0.6215*cur_weather - 11.37* wind**0.16 + 0.3965 * cur_weather* wind_ten**0.16
        if twc < -5 and twc > -20:
            clothes +="Надень пуховик и теплую кофту \U0001F9E4"
        elif twc <= -20:
            clothes +="Надень теплую зимнюю куртку и не забудь шарф \U0001F9E4"
        elif twc >= -5 and twc < 0:
            clothes +="Сегодня надень свитшот и весенную куртку \U0001F9E5"
        elif twc >= 0 and twc < 10:
            clothes +="Сегодня стоит надень весенную куртку и толстовку с капюшоном \U0001F456"
        elif twc >= 10 and twc < 15:
            clothes +="Сегодня можно надеть лёгкую ветровку \U0001F45F"
        elif twc >= 15:
            clothes +="Можешь смело надевать футболку и шорты \U0001F455 \U0001FA73"

        if wd == "Ясно \U00002600" and twc > 10:
            clothes +=",\nне забудь взять кепку) \U0001F9E2"
        elif (wd == "Дождь \U00002614" or wd == "Дождь \U00002614" or wd == "Гроза \U000026A1" ) and twc > 0:
            clothes +=",\nне забудь взять зонтик) \U00002602"

        await message.reply(f"Сегодня: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                            f"Погода в городе: {city}\nТемпература: {cur_weather}C° {wd}\n"
                            f"Влажность: {humidity}%\nДавление: {pressure} мм.рт.ст\nВетер: {wind} м/с\n"
                            )
        await bot.send_message(message.chat.id, f"{clothes}\n"f"Удачного тебе дня!")

        markup = standart_markup(message.from_user.id)

        await bot.send_message(message.chat.id, "Выбери дальнейшее действие", reply_markup=markup)
        await Form.base_state.set()
    except:
        await message.reply("\U0001F914 Проверьте название города и введите заново\U0001F504")
        await Form.weather_state.set()

@dp.message_handler(state=Form.remind_state)
async def get_remind(message: types.Message, state: FSMContext) -> None:
    text = message.text
    word = ":"
    ind = text.find(word)
    time_seconds = 0
    if (ind == 1):
        text = text.zfill(len(text) + 1)
        ind += 1
    try:
        time_1 = datetime.datetime.strptime(text[ind - 2: ind+len(word)+2],"%H:%M")
        time_2 = datetime.datetime.strptime(datetime.datetime.now().strftime("%H:%M"),"%H:%M")
        if ((time_1 - time_2).total_seconds() < 0):
            time_24 = datetime.datetime.strptime('23:59',"%H:%M")
            time_seconds = (time_24 - time_2).total_seconds() + time_1.hour*60*60 + time_1.minute*60
        else:
            time_seconds = (time_1 - time_2).total_seconds()
    except ValueError as e:
        print('Неверный формат')
        await bot.send_message(message.chat.id, "Неверный формат", reply_markup=standart_markup(message.from_user.id))
        await Form.base_state.set()

    try:
        db.set_remind(message.from_user.id, text[5:], str(time_1))
        await bot.send_message(message.chat.id, "Напоминание создано!)")
    except:
        await bot.send_message(message.chat.id, "Напоминание не создано", reply_markup=standart_markup(message.from_user.id))
        await Form.base_state.set()

    task_1 = asyncio.create_task(wait_time(time_seconds, message.chat.id, text[5:], message.from_user.id))
    task_2 = asyncio.create_task(Form.base_state.set())
    await task_1
    await task_2

async def wait_time(time, messageChatId, text, user_id) -> None:
    await asyncio.sleep(time)
    await bot.send_message(messageChatId, "Напоминаю: " + text)
    await db.delete_remind(user_id)

if __name__ == '__main__':
    executor.start_polling(dp)
