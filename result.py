import db
import codecs

def get():
    print('получаем результаты')
    query = """SELECT votes.telegram_chat_id, votes.name, f1.name AS za_kogo, f2.name AS ot_kogo, (SELECT count(users.tg_chat_id)  FROM users WHERE tg_chat_id=votes.telegram_chat_id) FROM votes
    INNER JOIN users ON votes.telegram_chat_id = users.tg_chat_id
    INNER JOIN faculties f1 ON votes.faculty_id  = f1.id
    INNER JOIN faculties f2 ON users.faculty_id  = f2.id
    WHERE users.faculty_id=(CASE WHEN (SELECT count(users.tg_chat_id)  FROM users WHERE tg_chat_id=votes.telegram_chat_id) = 2 THEN 20 ELSE users.faculty_id END) AND votes.event_id=2;"""
    # query = "SELECT sqlite_version()"
    result = db.execute_read_query(query)
    # перевариваем запрос из базы
    votes = {}
    for item in result:
        votes[item[0]] = [item[3]]
    for item in result:
        votes[item[0]].append(item[2])
    # выплёвываем в файл
    f = codecs.open('votes.csv', 'w', "utf-8")
    f.write(u'\ufeff')
    f.write('tg_chat_id;от кого; за кого;\n')
    for k, v in votes.items():
        f.write(k + ";")
        for item in v:
            f.write(item + ";")
        f.write("\n")
    f.close()
