import pytest
import requests
from config import Config
from tests.conftest import generate_random_text, get_all_tasks_as_dict_from_test_db
from app.task import Statuses


# Перед каждым тестом очищается тестовая табличка, id первой созданной задачи всегда будет равен 1.
# Почти все единички в тестах именно поэтому.
class TestCreateTask:
    """Тесты на POST запрос. Создание задачи."""
    @staticmethod
    def test_create_task_with_valid_req_body(truncate_tasks_table):
        # Arrange
        data = {'content': generate_random_text()}
        # Act
        req = requests.post(Config.complex_url, data)
        tasks = get_all_tasks_as_dict_from_test_db()
        # Assert
        assert req.status_code == 201
        assert req.text == str(1)
        assert tasks[1].get('content') == data.get('content')

    @staticmethod
    def test_create_task_with_invalid_req_body(truncate_tasks_table):
        # Arrange
        data = {'invalid_key': 'invalid_value'}
        # Act
        req = requests.post(Config.complex_url, data)
        # Assert
        assert req.status_code == 400


class TestGetAllTasks:
    """Тесты на GET запрос. Чтение всех записей из таблички."""
    @staticmethod
    def test_get_all_tasks(truncate_tasks_table, create_many_tasks):
        # Arrange
        count_of_created_tasks = create_many_tasks
        # Act
        req = requests.get(Config.complex_url)
        dict_of_tasks = req.json()
        # assert
        assert len(dict_of_tasks) == count_of_created_tasks

    @staticmethod
    def test_get_all_tasks_from_empty_table(truncate_tasks_table):
        # Act
        req = requests.get(Config.complex_url)
        # Assert
        assert len(req.json()) == 0


class TestDeleteTask:
    """Тесты на DELETE запрос. Удаление задачи."""
    @staticmethod
    def test_delete_task(truncate_tasks_table, create_task):
        # Act
        requests.delete(Config.complex_url + '/1')
        dict_of_tasks = get_all_tasks_as_dict_from_test_db()
        # Assert
        assert len(dict_of_tasks) == 0

    @staticmethod
    def test_delete_task_with_invalid_id(truncate_tasks_table):
        # Act
        req = requests.delete(Config.complex_url + '/1')
        # Assert
        assert req.status_code == 404


class TestUpdateTask:
    """Тесты для PUT запроса. Изменение задачи."""
    @staticmethod
    def test_update_content(truncate_tasks_table, create_task):
        # Arrange
        data = {'task_id': 1,
                'content': generate_random_text()}
        # Act
        requests.put(Config.complex_url, data)
        task = get_all_tasks_as_dict_from_test_db().get(1)
        # Assert
        assert task.get('content') == data.get('content')

    @staticmethod
    def test_update_status(truncate_tasks_table, create_task):
        # Arrange
        data = {'task_id': 1,
                'status': Statuses.new.value}
        # Act
        requests.put(Config.complex_url, data)
        # Выполним запрос в бд и достанем только что обновленную задачу, 1 - это ее ид.
        task_from_db = get_all_tasks_as_dict_from_test_db().get(1)
        # Assert
        assert task_from_db.get('current_status') == data.get('status')

    @staticmethod
    def test_update_content_and_status(truncate_tasks_table, create_task):
        # Arrange
        data = {'task_id': 1,
                'status': Statuses.new.value,
                'content': generate_random_text()}
        # Act
        requests.put(Config.complex_url, data)
        task_from_db = get_all_tasks_as_dict_from_test_db().get(1)
        # Assert
        assert task_from_db.get('current_status') == data.get('status')
        assert task_from_db.get('content') == data.get('content')

    @staticmethod
    def test_update_task_with_extra_param_in_req_body(truncate_tasks_table, create_task):
        # Arrange
        data = {'task_id': 1,
                'status': Statuses.new.value,
                'extra_value': 'extra value'}
        # Act
        req = requests.put(Config.complex_url, data)
        # Assert
        assert req.status_code == 400

    @staticmethod
    def test_update_not_existing_task(truncate_tasks_table):
        # Arrange
        data = {'task_id': 1,
                'status': Statuses.new.value}
        # Act
        req = requests.put(Config.complex_url, data)
        # Assert
        assert req.status_code == 404

    @staticmethod
    def test_update_task_only_with_task_id_in_req_body(truncate_tasks_table, create_task):
        # Arrange
        data = {'task_id': 1}
        # Act
        req = requests.put(Config.complex_url, data)
        # Assert
        assert req.status_code == 400

    @staticmethod
    def test_update_task_with_empty_req_body(truncate_tasks_table):
        # Arrange
        data = dict()
        # Act
        req = requests.put(Config.complex_url, data)
        # Assert
        assert req.status_code == 400


if __name__ == '__main__':
    pytest.main()
