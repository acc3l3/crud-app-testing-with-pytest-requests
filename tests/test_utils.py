import pytest
from app.utils import TaskUtils
from tests.conftest import get_all_tasks_as_dict_from_test_db


class TestTaskUtils:
    """Тесты для функций из app.utils TaskUtils"""
    @staticmethod
    def test_create_new_task(truncate_tasks_table):
        # Act
        new_task_id = TaskUtils.create_new_task()
        all_tasks = get_all_tasks_as_dict_from_test_db()
        # Assert
        assert new_task_id == 1
        assert len(all_tasks) == 1, 'Количество записей в таблице != 1. Скорее всего, запись не создалась.'

    @staticmethod
    def test_get_task_as_dict(truncate_tasks_table, create_task_with_attributes):
        # Act
        # Перед каждый тестом тестовая табличка очищается, поэтому id у первой созданной задачи в тесте будет равен 1.
        task = TaskUtils.get_task_as_dict(1)
        # Assert
        assert task.get('content') == create_task_with_attributes.get('content')
        assert task.get('date_of_creation') == create_task_with_attributes.get('date_of_creation')
        assert task.get('current_status') == create_task_with_attributes.get('current_status')
        assert task.get('previous_status') == create_task_with_attributes.get('previous_status')
        assert task.get('last_change_status_date') == create_task_with_attributes.get('last_change_status_date')

    @staticmethod
    def test_get_task_as_dict_with_invalid_id(truncate_tasks_table):
        """Если передан task_id, которого нет в табличке, то должно вызываться исключение"""
        with pytest.raises(ValueError):
            TaskUtils.get_task_as_dict(1)

    @staticmethod
    def test_get_all_tasks_as_dict(truncate_tasks_table, create_task_with_attributes, create_many_tasks):
        # Arrange
        # Добавим id = 1 в словарь, чтобы словари create_task_with_content и dict_of_tasks.get(1) были идентичными
        create_task_with_attributes.update({'id': 1})
        # Act
        dict_of_tasks = TaskUtils.get_all_tasks_as_dict()
        # Assert
        # +1 потому что перед create_many_tasks была создана еще 1 задача
        assert len(dict_of_tasks) == create_many_tasks + 1, 'Количество задач, которые попали в словарь, ' \
                                                            'не соответствует количеству задач в таблице'
        assert dict_of_tasks.get(1) == create_task_with_attributes

    @staticmethod
    def test_get_all_tasks_as_dict_with_zero_tasks_in_table(truncate_tasks_table):
        """Если в таблице нет задач, то функция должна вернуть пустой словарь"""
        # Act
        dict_of_tasks = TaskUtils.get_all_tasks_as_dict()
        # Assert
        assert isinstance(dict_of_tasks, dict)
        assert len(dict_of_tasks) == 0


if __name__ == '__main__':
    pytest.main()

