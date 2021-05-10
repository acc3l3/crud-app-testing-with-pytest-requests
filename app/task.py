from datetime import date
from enum import Enum
from app.connectdb import connect_db
from pydantic import BaseModel, root_validator
from typing import Optional
from config import Config
from datetime import datetime


class Statuses(Enum):
    """Валидные статусы для задачи. new - обязательный. Остальные используются только для валидации"""
    new = 'Waiting'
    in_progress = 'In progress'
    final = 'Done'


class UpdateTaskRequestBody(BaseModel):
    """Валидирует тело запроса на обновление задачи"""
    # Optional позволяет не передавать атрибуты через тело запроса и делает значение у таких атрибутов равным None
    task_id: int
    status: Optional[Statuses]
    content: Optional[str]

    # Удаляет такие атрибуты, которые не были переданы через тело запроса
    @root_validator
    def delete_none_values(cls, values):
        values_copy = values.copy()
        for key in values:
            if values[key] is None:
                values_copy.pop(key)
        if len(values_copy) == 1:
            raise ValueError('PUT request required also status and / or content')
        return values_copy

    class Config:
        extra = 'forbid'
        use_enum_values = True


class CreateTaskRequestBody(BaseModel):
    """Валидирует тело запроса на создание новой задачи"""
    content: str

    class Config:
        extra = 'forbid'


class Task:
    @connect_db
    def __init__(self, **kwargs):
        """Если был передан task_id, то будет создан инстанс класса с заполнеными атрибутами из таблички с задачами.
        Если не был передан task_id, то будет создана в бд новая задача с статусом Новая и текущей датой создания"""

        cursor = kwargs.get('cursor')
        self.task_id = kwargs.get('task_id')

        # Если не был передан task_id, то создадим новую задачу
        if self.task_id is None:
            self.date_of_creation = datetime.now()
            self._current_status = Statuses.new.value
            # В таблице с задачами создаем новую запись с текущей датой и статусом для новой задачи
            cursor.execute(f"INSERT INTO {Config.tasks_table_name} (date_of_creation, current_status) "
                           f"VALUES ('{datetime.now()}', '{Statuses.new.value}');")
            # Этот запрос вычисляет последний созданный id'шник в таблице с последовательностью id, он и будет task_id
            cursor.execute(f"SELECT CURRVAL ('{Config.tasks_table_name + '_id_seq'}');")
            self.task_id = cursor.fetchone()[0]
        # Если был передан task_id, то попытаемся найти такую задачу и установить атрибуты инстанса из бд
        else:
            cursor.execute(f"SELECT * FROM {Config.tasks_table_name} WHERE id = {self.task_id};")
            # Если не нашлось, задачи с таким task_id, то в task_values будет None
            task_values = cursor.fetchone()
            # Если в task_values None, то задачи с таким task_id нет, вызовем исключение по этому поводу
            if task_values is None:
                raise ValueError(f'Task with task_id = {task_id} not exist')
            # Соеденим атрибуты задачи и имена колонок в словарь
            column_names = Config.get_column_names()
            task_dict = dict()
            for key, value in zip(column_names, task_values):
                task_dict.update({key[0]: value})

            # Присвоим атрибутам инстанса значения из соответствующих ячейках в таблице с задачами,
            # c именами колонок и содержимым ячеек
            self._content = task_dict['content']
            self.date_of_creation = task_dict['date_of_creation']
            self.last_change_status_date = task_dict['last_change_status_date']
            self._current_status = task_dict['current_status']
            self.previous_status = task_dict['previous_status']

    def dict(self):
        """Возвращает атрибуты задачи в виде словаря {атрибут: значение}"""

        task_attributes = self.__dict__
        # В силу особенностей реализации модели задачи, некоторые атрибуты имеют _ в начале имени атрибута
        # В цикле пройдемся по всем ключам словаря с атрибутами и заменим ключи с _ на такие же, но без _
        updated_task_attributes = task_attributes.copy()
        for key in task_attributes:
            if str(key)[0] == '_':
                updated_task_attributes[str(key)[1:]] = updated_task_attributes.pop(key)
        return updated_task_attributes



    @connect_db
    def delete(self, cursor) -> None:
        """Удаляет задачу из таблицы с задачами"""
        cursor.execute(f"DELETE FROM {Config.tasks_table_name} WHERE id = {self.task_id};")

    @property
    def content(self):
        return self._content

    @content.setter
    @connect_db
    def content(self, content, cursor):
        """После обновления атрибута сразу же обновит его в таблице с задачами"""
        self._content = content
        cursor.execute(f"UPDATE {Config.tasks_table_name} SET content = '{self._content}' WHERE id = '{self.task_id}';")

    @property
    def current_status(self):
        return self._current_status

    @current_status.setter
    @connect_db
    def current_status(self, new_status, cursor):
        """
        Заменяет текущий статус на новый, если они отличаются. Текущий становится становится previous_status и в бд тоже
        """
        if self._current_status != new_status:
            self.previous_status = self._current_status
            self._current_status = new_status
            cursor.execute(f"UPDATE {Config.tasks_table_name} "
                           f"SET "
                           f"current_status = '{self._current_status}', "
                           f"previous_status = '{self.previous_status}', "
                           f"last_change_status_date = '{date.today()}' "
                           f"WHERE id = '{self.task_id}';")

    @staticmethod
    @connect_db
    def get_all_tasks_as_dict(cursor):
        """Возвращает словарь {task_id1: {attr1: value1, attr2: value2,..}, task_id2:..}"""

        # Получим все задачи из таблицы, отсортированные по id
        cursor.execute(f"SELECT * FROM {Config.tasks_table_name} ORDER BY id;")
        raw_tasks = cursor.fetchall()

        column_names = Config.get_column_names()
        tasks_dict = dict()

        # Для каждой задачи соединим названия колонок и атрибуты задачи в словарь
        for i in range(len(raw_tasks)):
            current_task = raw_tasks[i]
            current_task_dict = dict()
            for col_name, value in zip(column_names, current_task):
                current_task_dict.update({col_name[0]: value})
            # Добавим словарь текущей задачи к общему словарю со всеми задачами
            tasks_dict.update({current_task_dict.get('id'): current_task_dict})

        return tasks_dict
