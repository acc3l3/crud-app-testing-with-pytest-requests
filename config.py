from dataclasses import dataclass
from typing import Union
from os import environ
from contextlib import closing
from psycopg2 import connect


@dataclass
class Config:
    dbname: str = 'testdb'
    user: str = environ['dbuser']
    password: Union[str, int] = environ['dbpass']
    host: str = 'localhost'
    tasks_table_name: str = 'test_tasks'
    base_url: str = 'http://127.0.0.1:5000'
    endpoint: str = '/api/v1/tasks'
    complex_url: str = base_url + endpoint

    # Не помню почему именно здесь этот метод, но ему тут удобно
    @classmethod
    def get_column_names(cls) -> list:
        """Возвращает все имена колонок таблицы Config.tasks_table_name"""
        # Запрос достает имена имена колонок таблицы Config.tasks_table_name в том порядке, в котором они расположены
        with closing(connect(dbname=cls.dbname, user=cls.user, password=cls.password, host=cls.host)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT attname FROM pg_attribute WHERE attrelid = '{cls.tasks_table_name}'"
                    f"::regclass AND attnum > 0 ORDER BY attnum;")
                column_names = cursor.fetchall()
        return column_names
