import pytest
from app.task import UpdateTaskRequestBody, CreateTaskRequestBody, Task, Statuses
from pydantic import ValidationError
from tests.conftest import generate_random_text, get_all_tasks_as_dict_from_test_db


class TestUpdateTaskRequestBody:
    @staticmethod
    @pytest.mark.parametrize('req_body', [{'task_id': 1, 'status': Statuses.new.value},
                                          {'task_id': 1, 'status': Statuses.final.value, 'content': 'optional str'}])
    def test_with_valid_request_body(req_body):
        # Act
        validated_req_body = UpdateTaskRequestBody(**req_body)
        # Assert
        assert validated_req_body == req_body

    @staticmethod
    def test_with_extra_param_in_request_body():
        # Arrange
        req_body = {'task_id': 1, 'new_extra_param': True}
        # Act & Assert
        with pytest.raises(ValidationError):
            UpdateTaskRequestBody(**req_body)

    @staticmethod
    @pytest.mark.parametrize('req_body', [{'task_id': 'some string'},
                                          {'task_id': 1, 'status': 'Random status for test'}])
    def test_with_invalid_type_of_params_in_request_body(req_body):
        # Act & Assert
        with pytest.raises(ValidationError):
            UpdateTaskRequestBody(**req_body)

    @staticmethod
    def test_with_only_task_id_in_req_body():
        # Arrange
        req_body = {'task_id': 1}
        # Act & Assert
        with pytest.raises(ValidationError):
            UpdateTaskRequestBody(**req_body)

    @staticmethod
    def test_without_task_id_in_req_body():
        # Arrange
        req_body = {'status': 'some status', 'content': 'some content'}
        # Act & Assert
        with pytest.raises(ValidationError):
            UpdateTaskRequestBody(**req_body)


class TestCreateTaskRequestBody:
    @staticmethod
    def test_with_valid_req_body():
        # Arrange
        req_body = {'content': 'this is task content'}
        # Act
        validated_req_body = CreateTaskRequestBody(**req_body)
        # Assert
        assert req_body == validated_req_body

    @staticmethod
    def test_with_extra_param_in_request_body():
        # Arrange
        req_body = {'content': 'this is task content',
                    'extra_param': True}
        # Act & Assert
        with pytest.raises(ValidationError):
            CreateTaskRequestBody(**req_body)

    @staticmethod
    def test_without_required_param():
        # Arrange
        req_body = {'extra_param': True}
        # Act & Assert
        with pytest.raises(ValidationError):
            CreateTaskRequestBody(**req_body)


class TestTask:
    """Тесты для класса Task"""
    @staticmethod
    def test_create_new_task(truncate_tasks_table):
        """При вызове Task() должна быть создана новая задача"""
        # Act
        Task()
        all_tasks_from_db = get_all_tasks_as_dict_from_test_db()
        # Assert
        assert len(all_tasks_from_db) == 1

    @staticmethod
    def test_get_existing_task(truncate_tasks_table, create_task_with_attributes):
        """При вызове Task(task_id) должен быть создан экземпляр класса Task с атрибутами задачи"""
        # Arrange
        task_attributes = create_task_with_attributes
        # Act
        task = Task(1)
        # Assert
        assert task.content == task_attributes['content']
        assert task.date_of_creation == task_attributes['date_of_creation']
        assert task.current_status == task_attributes['current_status']
        assert task.previous_status == task_attributes['previous_status']
        assert task.last_change_status_date == task_attributes['last_change_status_date']

    @staticmethod
    def test_delete_task(truncate_tasks_table, create_task):
        # Act
        task = Task(1)
        task.delete()
        # Assert
        assert len(get_all_tasks_as_dict_from_test_db()) == 0

    @staticmethod
    def test_set_content(truncate_tasks_table, create_task):
        # Arrange
        new_task_content = generate_random_text()
        # Act & Assert
        task = Task(1)
        task.set_content(new_task_content)
        # Проверим что атрибут у экземляра класса поменялся
        assert task.content == new_task_content
        # Заново достанем задачу из бд и убедимся что и в бд поменялся контент у задачи
        task = Task(1)
        assert task.content == new_task_content

    @staticmethod
    def test_set_status(truncate_tasks_table, create_task_with_attributes):
        # Arrange
        new_status = generate_random_text()
        task = Task(1)
        # Act
        task.set_status(new_status)
        # Assert
        # Проверим что атрибуты у экземляра класса поменялись
        assert task.current_status == new_status
        assert task.previous_status == create_task_with_attributes['current_status']
        # Заново достанем задачу из бд и убедимся что и в бд поменялся статус у задачи
        task = Task(1)
        assert task.current_status == new_status
        assert task.previous_status == create_task_with_attributes['current_status']


if __name__ == '__main__':
    pytest.main()
