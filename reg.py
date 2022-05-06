from telebot import types
from telebot.types import Message
from telebot import TeleBot
import re
from answer import Answers
import db

answ = Answers()


def mailing(tg_chat_id):
    query = 'SELECT * FROM mailing WHERE tg_chat_id="{}"'.format(tg_chat_id)
    res = db.execute_read_query(query)
    if len(res) == 0:
        query = 'INSERT INTO mailing ("tg_chat_id") VALUES (\'{}\');'.format(tg_chat_id)
        db.execute_query(query)


def is_registered(tg_chat_id):
    query = "SELECT * FROM users WHERE tg_chat_id={};".format(tg_chat_id)
    result = db.execute_read_query(query)
    return len(result) > 0


def write_register_info(tg_chat_id, faculty_id, group, ignore = False):
    query = 'SELECT * FROM users WHERE in_group="{}"'.format(group.lower())
    res = db.execute_read_query(query)
    if len(res) == 0 or ignore:
        query = "INSERT INTO users (tg_chat_id, faculty_id, in_group) VALUES ('{}', {}, '{}');".format(tg_chat_id,
                                                                                                       faculty_id,
                                                                                                       group.lower())
        db.execute_query(query)
        return True
    else:
        return False


def back_to_start(tg_chat_id, bot: TeleBot):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=False)
    markup.add(types.KeyboardButton('👤 Я сотрудник'))
    markup.add(types.KeyboardButton('👨‍🎓 I am a foreign student'))
    bot.send_message(tg_chat_id, answ.need_registartion, parse_mode="MarkdownV2",
                     reply_markup=markup)


def get_faculty_by_st(login):
    pattern_st = r'^st[0-9]{6}$'
    id = 0
    if not re.search(pattern_st, login.lower()) is None:
        query = 'SELECT faculty FROM stBase WHERE login=\'{}\''.format(login.lower())
        result = db.execute_read_query(query)
        if len(result) > 0:
            id = result[0][0]
    elif login == '👤 Я сотрудник':
        id = 31
    elif login == '👨‍🎓 I am a foreign student':
        id = 20
    elif login == '⏪ Cancel':
        id = -1
    return id


def get_faculty_by_group(group):
    faculty_letter = {
        "пу": 22, "с": 5, "б": 17, "в": 11, "вшж": 21, "и": 16, "ии": 10, "вк": 10, "ики": 27, "мкн": 23, "мм": 15,
        "м": 1, "мо": 7, "вшм": 18, "нз": 3, "ип": 25, "фл": 19, "си": 26, "пл": 13, "пс": 6, "ст": 8, "фз": 9, "иф": 4,
        "х": 24, "э": 14, "ю": 12
    }
    inyaz = ['19.Б04-с', '19.Б05-э', '19.Б06-э', '20.Б01-мо', '20.Б05-вшм', '20.Б06-э', '20.Б07-э', '20.Б08-э',
             '20.Б09-э',
             '20.Б09-э', '20.Б11-мм', '20.Б12-мо', '20.М02-пс', '21.Б02-ии', '21.Б02-ю', '21.Б03-с', '21.Б06-и',
             '21.Б09-мо', '21.Б11-ю', '21.Б29-фл', '21.Б29-фл', '21.БО3-с', '21.М02-ии', '21.М10-ПУ', '21.М28-нз',
             '21.С06-м', 'Б06-нз.21', '20.м90-фл', '20.м95-фл', '20.м96-фл', '21.м90-фл', '21.м95-фл', '21.м96-фл',
             '20.м92-фл', '21.м92-фл', '20.м93-фл', '21.м93-фл', '20.м94-фл', '21.м94-фл', '20.м91-фл', '20.м97-фл',
             '21.м91-фл', '21.м97-фл']
    pattern_abms = r'^[12][0-9][.][абмс][0-9]{2}-[а-я]{1,3}$'
    pattern_ag_1 = r'^[89][екм][12]$'
    pattern_ag_2 = r'^1[01][бгикмд][12]$'
    pattern_fizra = r'^[012789]{2}[12][34][0-9]фк$'
    pattern_med_1 = r'^2[0-1]\.ом\..+$'
    pattern_med_2 = r'^[12][019]\.а[мпднф]{2,4}$'
    pattern_stom_1 = r'^2[0-1]\.ос\..+$'
    pattern_stom_2 = r'^[12][109]\.астом$'
    pattern_spo_med_stom = r'^[12]\-[12][016789]$'

    id = 0
    # ИнЯз 2
    if not re.search(pattern_abms, group.lower()) is None:
        str = group.lower().split('-')
        if str[1] == "фл" and group.lower() in inyaz:
            id = 2
        else:
            id = faculty_letter.get(str[1], 0)
    # АГ 28
    elif not re.search(pattern_ag_1, group.lower()) is None or not re.search(pattern_ag_2, group.lower()) is None:
        id = 28
    # ФизКолледж 29
    elif not re.search(pattern_fizra, group.lower()) is None:
        id = 29
    # Мадицина 1
    elif not re.search(pattern_med_1, group.lower()) is None or not re.search(pattern_med_2, group.lower()) is None:
        id = 1
    # Стоматология 8
    elif not re.search(pattern_stom_1, group.lower()) is None or not re.search(pattern_stom_2, group.lower()) is None:
        id = 8
    # СПО стомат + мед
    elif not re.search(pattern_spo_med_stom, group.lower()) is None:
        id = 30
    elif group == '👤 Я сотрудник':
        id = 31
    elif group == '👨‍🎓 I am a foreign student':
        id = 20
    elif group == '⏪ Cancel':
        id = -1
    return id
