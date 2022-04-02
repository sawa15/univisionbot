from telebot import types


class Answers:
    def __init__(self):
        self.start_text = (u'Привет!\n\n'
                           u'Ты здесь, а значит Унивидение 2022 началось! Участники уже выступили, и теперь исход конкурса зависит от тебя.\n\n'
                           u'Правила:\n'
                           u'🔘 Ты можешь проголосовать за нескольких участников, но у тебя НЕ будет возможности проголосовать за свой факультет!\n'
                           u'🔘 Да, мы понимаем, как хочется поддержать друзей, но давай помнить о том, что так победит самый талантливый претендент, а не самый общительный.\n\n'
                           u'Скорее нажимай на кнопку — пришло время творить историю, и прямо сейчас судьба участников находится в твоих руках!')
        self.start_button_text = '🟢 Голосовать!'
        self.event_closed = 'Голосование закрыто. Приходи в следующий раз.'
        self.error = '❌ Произошла ошибка. Введите /reset'
        self.need_registartion = (u'*Давай сначала зарегистрируемся*\n\n'
                                  u'Введи свой номер группы в официальном формате \(как указан в timetable\)\n'
                                  u'_Например: *21\.У04\-ни*_\n\n'
                                  u'Если вы сотрудник СПбГУ, нажмите соответсвующую кнопку\.'
                                  u'На следующем этапе вас попросят ввести свой *st*\n\n')
        self.need_registartion_eng = (u'*Let\\\'s register first*\n\n'
                                      u'Enter your official group number \(as it is listed on timetable\.spbu\.ru\)\n'
                                      u'_For example\:_ *21\.У04\-ни* _\(Cyrillic letters\)_')
        self.need_registartion_empl = u'Введите свой логин единой учётной записи в формате *stXXXXXX* \(X \- 6 цифр\)\n\n'

    def start_button(self):
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add(types.KeyboardButton(self.start_button_text))
        return markup


def employee_button():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton('👤 Я сотрудник'))
    return markup
