from contextlib import contextmanager
from psycopg2 import pool
from config import Config

connection_pool = pool.SimpleConnectionPool(minconn=1,
                                            maxconn=20,
                                            dbname=Config.dbname,
                                            host=Config.host,
                                            user=Config.user,
                                            password=Config.password)


def close_connection_pool():
    connection_pool.closeall()


@contextmanager
def get_connection():
    # Контекстный менеджер для получения подключения из пула подключений
    connection = connection_pool.getconn()
    try:
        yield connection
    # После выполнения запроса вернем подключение в пул подключений
    finally:
        connection_pool.putconn(connection)


def connect_db(func):
    """Подключаетс к базе данных c помощью декоратора, декорируемой функции обязательно нужно принять cursor"""
    def wrapper(*args, **kwargs):
        with get_connection() as conn:
            conn.autocommit = True
            cursor = conn.cursor()
        return func(*args, **kwargs, cursor=cursor)
    return wrapper
