import random
import pytest
from contextlib import closing
from psycopg2 import connect
from config import Config
from string import ascii_letters
from random import choice, randint
from datetime import date
from collections import OrderedDict
# Todo: Скорее всего, хранить вспомогательные функции в файлике conftest не лучшая затея, нужно будет изучить вопрос


def connect_db_for_tests(func) -> object:
    """Подключаетс к дб c помощью декоратора, декорируемой функции обязательно нужно принять cursor"""

    def wrapper(*args, **kwargs):
        with closing(connect(dbname=Config.dbname, user=Config.user, password=Config.password,
                             host=Config.host)) as conn:
            with conn.cursor() as cursor:
                conn.autocommit = True
                return func(*args, **kwargs, cursor=cursor)

    return wrapper


@connect_db_for_tests
def get_all_tasks_as_dict_from_test_db(cursor) -> dict:
    """
    Возвращает словарь со всеми задачами, где key - id задачи, а value - словарь из атрибутов задачи.
    task_id: int
    """

    # Получим сырые задачи из таблицы, отсортированные по id
    cursor.execute(f"SELECT * FROM {Config.tasks_table_name} ORDER BY id;")
    raw_tasks = cursor.fetchall()

    column_names = Config.get_column_names()
    dict_tasks = dict()

    # Для каждой задачи соединим названия колонок и атрибуты задачи в словарь
    for i in range(len(raw_tasks)):
        current_task = raw_tasks[i]
        current_task_dict = dict()
        for col_name, value in zip(column_names, current_task):
            current_task_dict.update({col_name[0]: value})
        # Добавим словарь текущей задачи к общему словарю со всеми задачами
        dict_tasks.update({current_task_dict.get('id'): current_task_dict})

    return dict_tasks


def generate_random_text(length: int = 30) -> str:
    """Генерирует и возвращает рандомную последовательность англ. букв разного регистра и пробела"""
    letters_with_space = ascii_letters + ' '
    return ''.join([choice(letters_with_space) for _ in range(length)])


# Todo эту штуку сделать autouse
@pytest.fixture()
@connect_db_for_tests
def truncate_tasks_table(cursor) -> None:
    """Очищает таблицу с задачами, сбрасывает счетчик id"""
    cursor.execute(f"TRUNCATE {Config.tasks_table_name} RESTART IDENTITY;")


@pytest.fixture()
@connect_db_for_tests
def create_task(cursor):
    """Создает задачу с непустым content, возвращает content"""
    content = generate_random_text()
    cursor.execute(f"INSERT INTO {Config.tasks_table_name} (date_of_creation) "
                   f"VALUES ('{date.today()}');")
    return content


@pytest.fixture()
@connect_db_for_tests
def create_many_tasks(cursor):
    """Создает несколько задач, возвращает количество созданных задач"""
    count_of_tasks = random.randint(1, 10)
    for _ in range(count_of_tasks):
        # Просто чтобы не создавать полностью пустые задачи
        content = generate_random_text()
        cursor.execute(f"INSERT INTO {Config.tasks_table_name} (content) "
                       f"VALUES ('{content}');")
    return count_of_tasks


@pytest.fixture()
@connect_db_for_tests
def create_task_with_attributes(cursor) -> dict:
    """Создает задачу и возвращает словарь с атрибутами этой задачи"""
    # OrderDict нужен потому что важен порядок атрибутов при составлении SQL запроса в exec_str
    task_attributes = OrderedDict(content=generate_random_text(40),
                                  date_of_creation=date(randint(1900, 2030), randint(1, 12), randint(1, 28)),
                                  current_status=generate_random_text(),
                                  previous_status=generate_random_text(),
                                  last_change_status_date=date(randint(1900, 2030), randint(1, 12), randint(1, 28)))
    exec_str = f"""INSERT INTO {Config.tasks_table_name} ({', '.join([key for key in task_attributes])}) VALUES ({', '.join([f"'{task_attributes[key]}'" for key in task_attributes])}); """
    cursor.execute(exec_str)
    return dict(task_attributes)
