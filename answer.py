from telebot import types


class Answers:
    def __init__(self):
        self.start_text = (u'Привет!\n\n'
                           u'Ты здесь, а значит Унивидение 2022 началось! Участники уже выступили, и теперь исход конкурса зависит от тебя.\n\n'
                           u'Правила:\n'
                           u'Ты можешь проголосовать за нескольких участников, но у тебя НЕ будет возможности проголосовать за свой факультет!\n\n'
                           u'Да, мы понимаем, как хочется поддержать друзей, но давай помнить о том, что так победит самый талантливый претендент, а не самый общительный.\n\n'
                           u'Скорее нажимай на кнопку — пришло время творить историю, и прямо сейчас судьба участников находится в твоих руках!')
        self.start_button_text = '🟢 Голосовать!'
        self.event_closed = 'Голосование закрыто. Приходи в следующий раз.'
        self.error = '❌ Произошла ошибка. Введите /reset'
        self.need_registartion = (u'*Давай сначала зарегистрируемся*\n\n'
                                  u'Введите свой логин единой учётной записи в формате stXXXXXX\n\n'
                                  u'Если вы сотрудник СПбГУ, нажмите соответсвующую кнопку\.')
        self.need_registartion_eng = (u'*Let\\\'s register first*\n\n'
                                      u'Please enter your personal SPbU student\\\'s ID \(stXXXXXX\)\n')
        self.need_registartion_empl = (u'Введите свой логин сотрудника в формате *stXXXXXX*\n\n'
                                       u'*В случае, если в написании логина будет допущена ошибка* – *голоса будут аннулированы после верификации*')

    def start_button(self):
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add(types.KeyboardButton(self.start_button_text))
        return markup


def employee_button():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton('👤 Я сотрудник'))
    return markup
