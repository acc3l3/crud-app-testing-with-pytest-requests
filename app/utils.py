from app.connectdb import connect_db
from config import Config
from datetime import datetime


class TaskUtils:
    @staticmethod
    @connect_db
    def create_new_task(cursor) -> int:
        """Content требуется передавать по значению. Создает новую задачу и возвращает ее id"""
        # Если не импортировать это прямо здесь, а в начале файла, то случится циклический импорт
        from app.task import Statuses
        cursor.execute(f"INSERT INTO {Config.tasks_table_name} (date_of_creation, current_status) "
                       f"VALUES ('{datetime.now()}', '{Statuses.new.value}');")
        # Этот запрос вычисляет последний созданный id'шник в таблице с последовательностью id
        cursor.execute(f"SELECT CURRVAL ('{Config.tasks_table_name + '_id_seq'}');")
        return cursor.fetchone()[0]

    @staticmethod
    @connect_db
    def get_task_as_dict(task_id: int, cursor):
        """Возвращает задачу как словарь, {Имя колонки: значение}"""
        cursor.execute(f"SELECT * FROM {Config.tasks_table_name} WHERE id = {task_id};")

        # Если не нашлось, задачи с таким task_id, то в task_values будет None
        task_values = cursor.fetchone()
        if task_values is None:
            raise ValueError(f'Task with task_id = {task_id} not exist')

        column_names = Config.get_column_names()

        task = dict()
        for key, value in zip(column_names, task_values):
            task.update({key[0]: value})
        return task

    @staticmethod
    @connect_db
    def get_all_tasks_as_dict(cursor):
        """Возвращает словарь {task_id1: {attr1: value1, attr2: value2,..}, task_id2...}"""

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
