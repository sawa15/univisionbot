import admin
import db
from datetime import datetime, timezone


# загрузка данных из базы
# список эвентов и соответсвие факультетов

def _get_current_event_db():
    """
    функция проверяет, следующие условия:
        - текущее значение времени находится после старта ивента, но до его окончания
        - список эвентов с условием выше единственный
    Если хотя бы одно не выполняется, то голосование считается закрытым
    :return:
    ID - голование открыто;
    False - голосование завершено, либо не началось, либо в базе данных ошибка
    """
    query = "SELECT * FROM 'events' WHERE ('events'.'start' < datetime('now') AND 'events'.'stop' > datetime('now'));"
    result = db.execute_read_query(query)

    len_result = len(result)
    if len_result != 1:
        if len_result > 1:
            admin.alarma("Алярма, в базе данных {} эвентов, которые происходят в один момент!!!".format(len_result))
        return None
    else:
        return result[0]


def _get_faculty_from_list_id_db(list_id):
    query = """SELECT faculties.id, faculties.name FROM facultyList
JOIN faculties ON faculties.id=facultyList.facultyID
WHERE facultyList.listID={}""".format(list_id)
    raw_result = db.execute_read_query(query)
    result = {}
    for item in raw_result:
        result[item[0]] = item[1]
    return result


def _get_all_faculties():
    query = "SELECT faculties.id, faculties.name FROM faculties"
    raw_result = db.execute_read_query(query)
    faculties = {}
    for item in raw_result:
        faculties[item[0]] = item[1]
    return faculties


def _get_admins():
    query = "SELECT admins.tg_chat_id FROM admins WHERE active = 1;"
    raw_result = db.execute_read_query(query)
    result = []
    for item in raw_result:
        result.append(item[0])
    return result


def _get_list_finished_voting_db(event_id):
    query = "SELECT tg_chat_id FROM finished_voting WHERE event_id = {}".format(event_id)
    raw_result = db.execute_read_query(query)
    result = []
    for item in raw_result:
        result.append(item[0])
    return result


def _get_all_vote_db(event_id):
    """
    ВОзвращает список всех голосов конкретного эвента один раз при инициализации локального кэша

    список вида {'tg_chat_id': ['от кого', 'за кого1', 'за кого2', 'за кого3'], ...}

    :param event_id:
    :return:
    """
#     query = """SELECT votes.telegram_chat_id, users.faculty_id as ot_kogo, votes.faculty_id as za_kogo  FROM votes
# INNER JOIN users ON votes.telegram_chat_id = users.tg_chat_id
# WHERE users.faculty_id= (SELECT iif((SELECT count(users.tg_chat_id)  FROM users WHERE tg_chat_id=votes.telegram_chat_id) = 2, 20, users.faculty_id)) AND votes.event_id={}""".format(
#         event_id)
    query = """SELECT votes.telegram_chat_id, users.faculty_id as ot_kogo, votes.faculty_id as za_kogo  FROM votes
INNER JOIN users ON votes.telegram_chat_id = users.tg_chat_id
WHERE users.faculty_id=(CASE WHEN (SELECT count(users.tg_chat_id)  FROM users WHERE tg_chat_id=votes.telegram_chat_id) = 2 THEN 20 ELSE users.faculty_id END) AND votes.event_id={}""".format(event_id)
    raw_result = db.execute_read_query(query)
    result = {}

    for item in raw_result:
        # result[item[0]] = [item[1]]
        result[item[0]] = []

    for item in raw_result:
        result[item[0]].append(item[2])

    return result


class LocalCache:
    def _reset_helper(self):
        event = _get_current_event_db()
        if event is None:
            admin.alarma("голосование закрыто")
            return None
        faculties = _get_faculty_from_list_id_db(event[5])
        admin.alarma("открыто голосование id:{} \"{}\"\nзакроется через {}".format(event[0], event[1],
                                                                                   datetime.strptime(event[3],
                                                                                                     "%Y-%m-%d %H:%M:%S") - datetime.utcnow()))
        return {'e': event, 'f': faculties}

    def __init__(self):
        result = self._reset_helper()
        self.admins = _get_admins()
        self.allfaculties = _get_all_faculties()
        if result is None:
            self.event_id = None
            self.event_name = None
            self.event_start = None
            self.event_stop = None
            self.event_amount_votes = None
            self.faculties = None
            self.finished_voting = []
            self.all_vote_list = {}
        else:
            self.event_id = result['e'][0]
            self.event_name = result['e'][1]
            self.event_start = datetime.strptime(result['e'][2], "%Y-%m-%d %H:%M:%S")
            self.event_stop = datetime.strptime(result['e'][3], "%Y-%m-%d %H:%M:%S")
            self.event_amount_votes = int(result['e'][4])
            self.faculties = result['f']
            self.finished_voting = _get_list_finished_voting_db(self.event_id)
            self.all_vote_list = _get_all_vote_db(self.event_id)

    def reset(self):  # переписать
        result = self._reset_helper()
        self.admins = _get_admins()
        self.allfaculties = _get_all_faculties()
        self.finished_voting = 0
        if result is None:
            self.event_id = None
            self.event_name = None
            self.event_start = None
            self.event_stop = None
            self.event_amount_votes = None
            self.faculties = None
            self.finished_voting = []
            self.all_vote_list = {}
            return False
        else:
            self.event_id = result['e'][0]
            self.event_name = result['e'][1]
            self.event_start = datetime.strptime(result['e'][2], "%Y-%m-%d %H:%M:%S")
            self.event_stop = datetime.strptime(result['e'][3], "%Y-%m-%d %H:%M:%S")
            self.event_amount_votes = int(result['e'][4])
            self.faculties = result['f']
            self.finished_voting = _get_list_finished_voting_db(self.event_id)
            self.all_vote_list = _get_all_vote_db(self.event_id)
            return True

    def check_current_event(self):
        """
        проверяем есть ли активное голосование
        если есть, то возвращаем event_id, иначе False
        :return:
        """
        if self.event_id is None:
            if not self.reset():
                return None

        if not ((datetime.utcnow() > self.event_start) and (datetime.utcnow() < self.event_stop)):
            if not self.reset():
                return None

        return self.event_id

    def get_amount_voting(self):
        return self.event_amount_votes

    def get_faculty_from_id(self, faculty_id):
        return self.faculties.get(int(faculty_id), "АХТУНГ!")

    def get_faculty_from_id_global(self, faculty_id):
        return self.allfaculties.get(int(faculty_id), "АХТУНГ!")

    def check_finish_voting(self, tg_chat_id):
        return str(tg_chat_id) in self.finished_voting

    def confirm_vote(self, tg_chat_id):
        if not self.check_finish_voting(tg_chat_id):
            self.finished_voting.append(str(tg_chat_id))
            query = "INSERT INTO finished_voting ('tg_chat_id', 'event_id') VALUES ('{}', '{}');".format(tg_chat_id,
                                                                                                         self.event_id)
            db.execute_query(query)
            return True
        return False

    def take_a_vote(self, tg_chat_id, faculty_id, name, username, event_id):
        # проверяем есть ли наш аккаунт в локальном кэше
        if self.all_vote_list.get(str(tg_chat_id), 0) == 0:
            self.all_vote_list[str(tg_chat_id)] = []
        if faculty_id in self.all_vote_list[str(tg_chat_id)]:
            admin.alarma("{} пытается проголосовать за проголосованный факультет".format(tg_chat_id))
            return False
        num_voting_left = self.event_amount_votes - len(self.all_vote_list[str(tg_chat_id)])
        if num_voting_left > 0:
            query = "INSERT INTO votes (telegram_chat_id, faculty_id, timestamp, name, username, event_id) VALUES ('{tg_chat_id}', '{faculty_id}', '{timestamp}', '{name}', '{username}', '{event_id}');".format(
                tg_chat_id=tg_chat_id, faculty_id=faculty_id,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), name=name, username=username,
                event_id=event_id)
            if db.execute_query(query):
                self.all_vote_list[str(tg_chat_id)].append(faculty_id)
                return True
            else:
                return False
        else:
            return False

    def get_num_voting_left(self, tg_chat_id):
        if self.all_vote_list.get(str(tg_chat_id), 0) == 0:
            self.all_vote_list[str(tg_chat_id)] = []
        return self.event_amount_votes - len(self.all_vote_list[str(tg_chat_id)])

    def get_num_voting_records(self, tg_chat_id):
        if self.all_vote_list.get(str(tg_chat_id), 0) == 0:
            self.all_vote_list[str(tg_chat_id)] = []
        return len(self.all_vote_list[str(tg_chat_id)])

    def delete_last_vote(self, tg_chat_id):
        print("типа удалили последний голос")
        if self.get_num_voting_records(tg_chat_id) == 0:
            return False

        faculty_id = self.all_vote_list[str(tg_chat_id)].pop()
        query = "DELETE FROM votes WHERE telegram_chat_id='{}' AND event_id='{}' AND faculty_id='{}';".format(tg_chat_id, self.event_id, faculty_id)
        if db.execute_query(query):
            return True
        else:
            self.all_vote_list[str(tg_chat_id)].append(faculty_id)
            return False


if __name__ == '__main__':
    lc = LocalCache()
    print(_get_all_vote_db(2))
    lc.take_a_vote(52899166, 1, "name", "username", 4)
    print(lc.all_vote_list)
    # print(lc.event_id)
    # print(lc.event_name)
    # print(lc.event_start)
    # print(lc.event_stop)
    # print(lc.event_amount_votes)
    # print(lc.faculties)
