
from datetime import date
from enum import Enum
from app.connectdb import connect_db
from pydantic import BaseModel, root_validator
from typing import Optional
from config import Config
from app.utils import TaskUtils


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
    def __init__(self, task_id: int = None):
        """Сделал из этого метода метод а-ля getOrCreate. Если id не передан, то создает задачу."""
        if task_id is not None:
            self.task_id = task_id
        else:
            self.task_id = TaskUtils.create_new_task()

        task_dict = TaskUtils.get_task_as_dict(self.task_id)
        self._content = task_dict['content']
        self.date_of_creation = task_dict['date_of_creation']
        self.last_change_status_date = task_dict['last_change_status_date']
        self._current_status = task_dict['current_status']
        self.previous_status = task_dict['previous_status']

    @connect_db
    def delete(self, cursor) -> None:
        cursor.execute(f"DELETE FROM {Config.tasks_table_name} WHERE id = {self.task_id};")

    @property
    def content(self):
        return self._content

    @content.setter
    @connect_db
    def content(self, content, cursor):
        self._content = content
        cursor.execute(f"UPDATE {Config.tasks_table_name} SET content = '{self._content}' WHERE id = '{self.task_id}';")

    @property
    def current_status(self):
        return self._current_status

    @current_status.setter
    @connect_db
    def current_status(self, new_status, cursor):
        """
        Заменяет текущий статус на новый, если они отличаются. Текущий становится становится previous_status.
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
