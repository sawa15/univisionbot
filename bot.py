import math
import re
from datetime import datetime, timezone
import telebot
from telebot import types
from telebot.types import Message

import db
import admin
import reg
import result
from preparation import LocalCache
import answer
import config
from answer import Answers

lc = LocalCache()
answ = Answers()

bot = telebot.TeleBot(config.API_TOKEN)


def get_faculty_list(event_id, tg_chat_id):
    """
    Функция возвращает список факультетов, которые учавствуют в текущем голосвании

    выводим таблицу с голосами, в которой чат телеграма совпадает с тем, кто нам написал,
    id эвента совпадает с текущим,
    """
    query = """SELECT DISTINCT faculties.id, faculties.name FROM facultyList
JOIN events ON events.list = facultyList.listID
JOIN faculties ON faculties.id = facultyList.facultyID
LEFT JOIN votes ON votes.faculty_id = facultyList.facultyID AND votes.event_id = events.id
WHERE events.id = {event_id}
EXCEPT
SELECT DISTINCT faculties.id, faculties.name FROM facultyList
JOIN faculties ON faculties.id = facultyList.facultyID
LEFT JOIN votes ON votes.faculty_id = facultyList.facultyID
WHERE votes.event_id = {event_id} AND votes.telegram_chat_id = {tg_chat_id}
EXCEPT
SELECT DISTINCT faculties.id, faculties.name FROM users
JOIN faculties ON users.faculty_id = faculties.id
WHERE tg_chat_id = {tg_chat_id}""".format(event_id=event_id, tg_chat_id=tg_chat_id)
    result = db.execute_read_query(query)
    return result


def get_faculty_keyboard(event_id, tg_chat_id, row_width=3):
    """
    Функция генерирует клавиатуру состояшую из факультетов, чтобы сразу высрать её пользователю
    :param event_id:
    :param tg_chat_id:
    :param row_width: ширина клавиатуры, по умолчанию "3"
    :return:
    """
    markup = types.InlineKeyboardMarkup(row_width=row_width)

    # вывожу кнопки с факультетами, если количество голосов не исчерпано
    num_voting_records = lc.get_num_voting_records(tg_chat_id)
    num_voting_left = lc.get_num_voting_left(tg_chat_id)
    if num_voting_left > 0:
        faculties = get_faculty_list(event_id, tg_chat_id)
        for i in range(0, math.ceil(len(faculties) / row_width) + 1):
            row = [types.InlineKeyboardButton(item[1], callback_data="{}__{}".format(event_id, item[0])) for item in
                   faculties[i * row_width:i * row_width + row_width]]
            markup.add(*row)
    if num_voting_records > 0:
        del_button = types.InlineKeyboardButton("⏪ Отменить последний выбор", callback_data="del__{}".format(event_id))
        markup.add(del_button)
        conf_button = types.InlineKeyboardButton("☑️ Завершить голосование", callback_data="conf__{}".format(event_id))
        markup.add(conf_button)

    return markup


def get_voted_list(event_id, tg_chat_id):
    query = """SELECT faculties.name FROM votes
JOIN faculties ON faculties.id=votes.faculty_id
WHERE votes.telegram_chat_id = {tg_chat_id} AND votes.event_id={event_id};""".format(tg_chat_id=tg_chat_id,
                                                                                     event_id=event_id)
    raw_result = db.execute_read_query(query)
    result = []
    for item in raw_result:
        result.append(item[0])
    return result


def get_num_voting_left(event_id, voted_list):
    return lc.get_amount_voting() - len(voted_list)


def get_vote_message_text(event_id, tg_chat_id):
    voting_left = ''
    if lc.get_num_voting_records(tg_chat_id) == 0:
        voting_left = 'Вы ещё ни за кого не проголосовали.'
    else:
        voted_list_str = ""
        for faculty_id in lc.all_vote_list[str(tg_chat_id)]:
            voted_list_str += "🔘 {}\n".format(lc.get_faculty_from_id_global(faculty_id))

        num_voting_left = lc.get_num_voting_left(tg_chat_id)
        ololol = {
            1: 'факультет',
            2: 'факультета',
            3: 'факультета',
            4: 'факультета'
        }
        try:
            faculty_str = ololol[num_voting_left]
        except KeyError as e:
            faculty_str = 'факультетов'

        if not num_voting_left == 0:
            voting_left = 'Осталось выбрать {num_voting_left} {faculty_str}\n\n'.format(num_voting_left=num_voting_left,
                                                                                        faculty_str=faculty_str)
        else:
            voting_left = "Завершите голосование!\n\n"
        voting_left += ('Учтёны голоса за следующие факультеты:\n'
                        '{voted_list_str}'.format(voted_list_str=voted_list_str))

    text = ('Выбери факультеты, которые тебе больше всего понравились!\n\n'
            '{voting_left}'.format(voting_left=voting_left))
    return text


def edit_vote_message(event_id, call, keyboard_width):
    markup = get_faculty_keyboard(event_id, call.from_user.id, keyboard_width)
    text = get_vote_message_text(event_id, call.from_user.id)
    bot.edit_message_text(text, call.from_user.id, call.message.id, reply_markup=markup)


# Handle '/start' and '/help' and '/reset'
@bot.message_handler(commands=['help', 'start', 'reset'])
def send_welcome(message):
    bot.send_message(message.chat.id, answ.start_text, reply_markup=answ.start_button())
    reg.mailing(message.chat.id)
    if str(message.chat.id) in lc.admins:
        db.execute_query(
            "DELETE FROM votes WHERE telegram_chat_id='{}' AND event_id='{}'".format(message.chat.id, lc.event_id))
        db.execute_query("DELETE FROM users WHERE tg_chat_id='{}'".format(message.chat.id))
        db.execute_query(
            "DELETE FROM finished_voting WHERE tg_chat_id='{}' AND event_id='{}'".format(message.chat.id, lc.event_id))


@bot.message_handler(commands=['resetlc'])
def resetlc_handler(message):
    if str(message.chat.id) in lc.admins:
        lc.reset()
        bot.send_message(message.chat.id, answ.start_text, reply_markup=answ.start_button())
    else:
        bot.send_message(message.chat.id, "Эта команда не для тебя", reply_markup=answ.start_button())


@bot.message_handler(commands=['result'])
def result_handler(message: Message):
    if str(message.chat.id) in lc.admins:
        data = message.text.split(' ')
        if not len(data) == 2:
            # можно будет выводить в будущем список эвентов
            bot.send_message(message.chat.id, "введи id голосования /result <id>", reply_markup=answ.start_button())
            return
        if not data[1].isnumeric():
            bot.send_message(message.chat.id, "в аргументе должно быть число", reply_markup=answ.start_button())
            return
        result.get(data[1])
        f = open('votes.csv', encoding="utf-8")
        bot.send_document(message.chat.id, f, reply_markup=answ.start_button())
        f.close()
    else:
        bot.send_message(message.chat.id, "Эта команда не для тебя", reply_markup=answ.start_button())


@bot.message_handler(commands=['vstart', 'vstop'])
def vstart_handler(message: Message):
    if str(message.chat.id) in lc.admins:
        data = message.text.split(' ')
        command = data[0]
        if not len(data) == 2:
            # можно будет выводить в будущем список эвентов
            bot.send_message(message.chat.id, "введи id голосования {} <id>".format(command),
                             reply_markup=answ.start_button())
            return
        if not data[1].isnumeric():
            bot.send_message(message.chat.id, "в аргументе должно быть число", reply_markup=answ.start_button())
            return
        if command == '/vstart':
            lc.start_voting(data[1])
        else:
            lc.stop_voting(data[1])
        bot.send_message(message.chat.id, "/reset", reply_markup=answ.start_button())

    else:
        bot.send_message(message.chat.id, "Эта команда не для тебя", reply_markup=answ.start_button())


@bot.message_handler(commands=['admin'])
def result_handler(message: Message):
    return

    if not (str(message.chat.id) in lc.admins):
        bot.send_message(message.chat.id, "Эта команда не для тебя", reply_markup=answ.start_button())
        return

    text = ""
    if lc.check_current_event() is None:
        text += 'Голосование сейчас закрыто\n\n'
    else:
        text += 'Открыто голосование "{name}"\nid: {id}\n\n'.format(name=lc.event_name, id=lc.event_id)

    text += 'получить результаты голосования: /result <id>\n'
    text += 'позже тут будет список всех голосований из базы\n\n'

    bot.send_message(message.chat.id, "акт", reply_markup=answ.start_button())


# Регистрация студентов, КИОшников и сотрудников
def register_handler_student(message: Message):
    # id = reg.get_faculty_by_group(message.text)
    if message.text == '/reset' or message.text == '/start':
        bot.send_message(message.chat.id, answ.start_text, reply_markup=answ.start_button())
        return

    id = reg.get_faculty_by_st(message.text)

    if id == 0:  # если не определился факультет
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=False)
        markup.add(types.KeyboardButton('👤 Я сотрудник'))
        markup.add(types.KeyboardButton('👨‍🎓 I am a foreign student'))
        bot.send_message(message.chat.id, "Такой логин не найден. Попробуй ещё раз",
                         reply_markup=markup)
        bot.register_next_step_handler(message, register_handler_student)
        return
    # если сотрудник
    elif id == 31:
        # переходим в другой степ где запрашиваем stXXXXXX
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton('⏪ Отмена'))
        bot.send_message(message.chat.id, answ.need_registartion_empl, reply_markup=markup,
                         parse_mode="MarkdownV2")
        bot.register_next_step_handler(message, register_handler_student_empl)
        return
    # если КИО
    elif id == 20:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton('⏪ Cancel'))
        bot.send_message(message.chat.id, answ.need_registartion_eng, reply_markup=markup,
                         parse_mode="MarkdownV2")
        bot.register_next_step_handler(message, register_handler_student_kio)
        return

    if not reg.write_register_info(message.chat.id, id, message.text):  # такой логин уже есть в базе
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=False)
        markup.add(types.KeyboardButton('👤 Я сотрудник'))
        markup.add(types.KeyboardButton('👨‍🎓 I am a foreign student'))
        bot.send_message(message.chat.id, "Ползователь с таким st уже зарегистрирован. Повторите ввод",
                         reply_markup=markup)
        admin.alarma(
            "Пытается ввести уже зарегистрированный {} id:{} {}\n\t@{} {} {}".format(
                message.text, id, lc.get_faculty_from_id_global(id), message.from_user.username,
                message.from_user.first_name, message.from_user.last_name))
        bot.register_next_step_handler(message, register_handler_student)
    else:  # регистрация прошла успешно
        print(u"{} --- {} @{} {} {}".format(message.text, lc.get_faculty_from_id_global(id), message.chat.username,
                                            message.chat.first_name, message.chat.last_name))
        bot.send_message(message.chat.id, "Поздравляю, ты справился. Жми на кнопку",
                         reply_markup=answ.start_button(), parse_mode="Markdown")


def register_handler_student_kio(message):
    if message.text == '⏪ Cancel':
        reg.back_to_start(message.chat.id, bot)
        bot.register_next_step_handler(message, register_handler_student)
        return
    if message.text == '/reset' or message.text == '/start':
        bot.send_message(message.chat.id, answ.start_text, reply_markup=answ.start_button())
        return

    id = reg.get_faculty_by_st(message.text)

    if id == 0:  # если не определился факультет
        bot.send_message(message.chat.id, "Такой логин не найден. Попробуй ещё раз")
        bot.register_next_step_handler(message, register_handler_student_kio)
        return
    # если сотрудник или КИО, то  он плохой
    elif id == 31 or id == 20:
        bot.send_message(message.chat.id, "А ты мелкик проказник. так нельзя!", reply_markup=answ.start_button())
        return

    if not reg.write_register_info(message.chat.id, id, message.text):  # такой логин уже есть в базе
        bot.send_message(message.chat.id, "Ползователь с таким st уже зарегистрирован. Повторите ввод")
        admin.alarma(
            "КИО Пытается ввести уже зарегистрированный {} id:{} {}\n\t@{} {} {}".format(
                message.text, id, lc.get_faculty_from_id_global(id), message.from_user.username,
                message.from_user.first_name, message.from_user.last_name))
        bot.register_next_step_handler(message, register_handler_student_kio)
    else:  # регистрация прошла успешно
        print(u"{} --- КИО + {} @{} {} {}".format(message.text, lc.get_faculty_from_id_global(id), message.chat.username,
                                            message.chat.first_name, message.chat.last_name))
        bot.send_message(message.chat.id, "Поздравляю, ты справился. Жми на кнопку",
                         reply_markup=answ.start_button(), parse_mode="Markdown")
        reg.write_register_info(message.chat.id, 20, message.text, True)


def register_handler_student_empl(message):
    if message.text == '⏪ Отмена':
        reg.back_to_start(message.chat.id, bot)
        bot.register_next_step_handler(message, register_handler_student)
        return
    if message.text == '/reset' or message.text == '/start':
        bot.send_message(message.chat.id, answ.start_text, reply_markup=answ.start_button())
        return

    id = reg.get_faculty_by_st(message.text)
    if not id == 0:  # если определился факультет, регистрируем как студента
        if id == 31 or id == 20:
            bot.send_message(message.chat.id, "А ты мелкик проказник. так нельзя!", reply_markup=answ.start_button())
            return
        else:
            if not reg.write_register_info(message.chat.id, id, message.text):  # такой логин уже есть в базе
                bot.send_message(message.chat.id, "Ползователь с таким st уже зарегистрирован. Повторите ввод")
                admin.alarma(
                    "Пытается ввести уже зарегистрированный {} id:{} {}\n\t@{} {} {}".format(
                        message.text, id, lc.get_faculty_from_id_global(id), message.from_user.username,
                        message.from_user.first_name, message.from_user.last_name))
                bot.register_next_step_handler(message, register_handler_student_empl)
            else:  # регистрация прошла успешно
                print(u"{} --- {} @{} {} {}".format(message.text, lc.get_faculty_from_id_global(id),
                                                    message.chat.username,
                                                    message.chat.first_name, message.chat.last_name))
                bot.send_message(message.chat.id, "Поздравляю, ты справился. Жми на кнопку",
                                 reply_markup=answ.start_button(), parse_mode="Markdown")
        return
    # если в базе нет, значит сотрудник
    else:
        if not reg.write_register_info(message.chat.id, 31, message.text):  # такой логин уже есть в базе
            bot.send_message(message.chat.id, "Ползователь с таким st уже зарегистрирован. Повторите ввод")
            admin.alarma(
                "Пытается ввести уже зарегистрированный {} id:{} {}\n\t@{} {} {}".format(
                    message.text, id, lc.get_faculty_from_id_global(id), message.from_user.username,
                    message.from_user.first_name, message.from_user.last_name))
            bot.register_next_step_handler(message, register_handler_student_empl)
        else:  # регистрация прошла успешно
            print(u"Сотрудник --- @{} {} {}".format(message.chat.username, message.chat.first_name,
                                                    message.chat.last_name))
            bot.send_message(message.chat.id, "Ура, можно перейти к голосованию\. Жми на кнопку",
                             reply_markup=answ.start_button(), parse_mode="MarkdownV2")
        return


def all_inspections(event_id, tg_chat_id):
    # проверяем есть ли действующее голосование
    if event_id is None:
        bot.send_message(tg_chat_id, answ.event_closed, reply_markup=answ.start_button())
        return False
    # Проверяем проголосовал ли человек в этом эвенте. Если да, то благодарим посылаем
    if lc.check_finish_voting(tg_chat_id):
        bot.send_message(tg_chat_id, "Вы уже проголосовали, ваш выбор записан.",
                         reply_markup=answ.start_button())
        return False
    return True


# # Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def start(message: Message):
    if message.text == "\U0001f7e2 Голосовать!":
        if not reg.is_registered(message.chat.id):
            reg.back_to_start(message.chat.id, bot)
            bot.register_next_step_handler(message, register_handler_student)
            return

        event_id = lc.check_current_event()
        # делает проверки на соответствие эвента, незавершённость голосования
        if not all_inspections(event_id, message.chat.id):
            return

        # создаём клавиатуру
        row_width = 3
        markup = get_faculty_keyboard(event_id, message.chat.id, row_width)
        text = get_vote_message_text(event_id, message.chat.id)

        s = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")


# если нажали на кнопку голосования
@bot.callback_query_handler(func=lambda call: re.match(r'^[0-9]+__[0-9]+$', call.data) is not None)
def callback_query(call):
    event_id = lc.check_current_event()
    split_data = call.data.split('__')
    call_event_id = split_data[0]
    call_faculty_id = split_data[1]
    if not all_inspections(event_id, call.from_user.id) or not event_id == int(call_event_id):
        bot.answer_callback_query(call.id, answ.error)
        return
    if not reg.is_registered(call.from_user.id):
        bot.answer_callback_query(call.id, answ.error)
        reg.back_to_start(call.from_user.id, bot)
        bot.register_next_step_handler(call.message, register_handler_student)
        return

    check_vote = lc.take_a_vote(call.from_user.id, call_faculty_id,
                                "{} {}".format(call.from_user.first_name, call.from_user.last_name),
                                call.from_user.username, call_event_id)
    if check_vote:
        bot.answer_callback_query(call.id, "✅ {}".format(lc.get_faculty_from_id(call_faculty_id)))
        print(u"@{username} проголосовал за {data} {first_name} {last_name} id:{id}".format(
            data=lc.get_faculty_from_id(call_faculty_id),
            username=call.from_user.username,
            first_name=call.from_user.first_name,
            last_name=call.from_user.last_name,
            id=call.from_user.id))
    else:
        bot.answer_callback_query(call.id, answ.error)
        return
    edit_vote_message(call_event_id, call, 3)


@bot.callback_query_handler(func=lambda call: re.match(r'^conf__[0-9]+$', call.data) is not None)
def confirmation(call):
    split_data = call.data.split('__')
    call_event_id = split_data[1]
    event_id = lc.check_current_event()
    if not all_inspections(event_id, call.from_user.id) or not event_id == int(call_event_id):
        bot.answer_callback_query(call.id, answ.error)
        return
    if not str(call_event_id) == str(lc.event_id):
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")
        return
    if lc.get_num_voting_records(call.from_user.id) == 0:
        bot.answer_callback_query(call.id, "❌ Проголосуй за кого-нибудь")
        return
    if not reg.is_registered(call.from_user.id):
        bot.answer_callback_query(call.id, answ.error)
        reg.back_to_start(call.from_user.id, bot)
        bot.register_next_step_handler(call.message, register_handler_student)
        return

    if lc.confirm_vote(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Ваше голосование сохранено (нет)")
        sponsor = "\n\nА пока мы считаем голоса, можете познакомиться с партнёрской студией трансляций, которая помогла нам сегодня показать участников во всей красе: bzstream.ru"
        # sponsor = ""
        bot.send_message(call.from_user.id, "Спасибо, что проголосовали{}".format(sponsor),
                         reply_markup=answ.start_button())
    else:
        bot.answer_callback_query(call.id, "❌ Повторно сохранить нельзя")
    bot.delete_message(call.from_user.id, call.message.id)


@bot.callback_query_handler(func=lambda call: re.match(r'^del__[0-9]+$', call.data) is not None)
def delete_last(call):
    split_data = call.data.split('__')
    call_event_id = split_data[1]
    event_id = lc.check_current_event()
    if not all_inspections(event_id, call.from_user.id) or not event_id == int(call_event_id):
        bot.answer_callback_query(call.id, answ.error)
        return
    if not str(call_event_id) == str(lc.event_id):
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")
        return
    if not reg.is_registered(call.from_user.id):
        bot.answer_callback_query(call.id, answ.error)
        reg.back_to_start(call.from_user.id, bot)
        bot.register_next_step_handler(call.message, register_handler_student)
        return
    if lc.delete_last_vote(call.from_user.id):
        bot.answer_callback_query(call.id, "Удалён последний вариант")
        edit_vote_message(call_event_id, call, 3)
    else:
        bot.answer_callback_query(call.id, "Не удалилось")
    # bot.answer_callback_query(call.id, "😢 Пока не работает 😢")
    # edit_vote_message(call_event_id, call, 3)


# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
bot.load_next_step_handlers()

bot.infinity_polling()
