import sqlite3
from sqlite3 import Error
import threading

connection = None
try:
    connection = sqlite3.connect('univision.db', check_same_thread=False)
except Error as e:
    print(e)

lock = threading.Lock()


def execute_query(query):
    with lock:
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            connection.commit()
            return True
        except Error as e:
            print(e)
            return False


def execute_read_query(query):
    with lock:
        cursor = connection.cursor()
        result = None
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(e)
