from contextlib import closing
from psycopg2 import connect
from config import Config


# Todo: переписать на использование connection pool
# The best practice is to create a single connection and keep it open as long as required.
# https://pynative.com/psycopg2-python-postgresql-connection-pooling/
def connect_db(func):
    """Подключаетс к базе данных c помощью декоратора, декорируемой функции обязательно нужно принять cursor"""
    def wrapper(*args, **kwargs):
        with closing(connect(dbname=Config.dbname,
                             user=Config.user,
                             password=Config.password,
                             host=Config.host)) as conn:
            with conn.cursor() as cursor:
                conn.autocommit = True
                return func(*args, **kwargs, cursor=cursor)
    return wrapper



