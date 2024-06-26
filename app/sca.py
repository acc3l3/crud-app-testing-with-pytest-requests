# Без этих 2-ух строчек не видно config.py
import sys
sys.path.append('../')
from flask import Flask, request, Response, redirect
from app.task import Task, UpdateTaskRequestBody, CreateTaskRequestBody
from pydantic import ValidationError
from connectdb import close_connection_pool
import atexit

app = Flask(__name__)


@app.route('/')
def root():
    return redirect('/api/v1/tasks')


@app.route('/api/v1/tasks', methods=['GET'])
def get_all_tasks():
    """Вернет все задачи из таблицы, если задач нет, то вернет пустой json"""
    return Task.get_all_tasks_as_dict()


@app.route('/api/v1/tasks', methods=['POST'])
def create_task():
    """Для создания задачи необходимо передать текст задачи, в случае успеха, вернет task_id, созданной задачи"""
    try:
        content = CreateTaskRequestBody(**request.form).content
    except ValidationError:
        return Response(status=400, response="The request body should contain only 1 parameter - content")
    else:
        task = Task()
        task.content = content
        return Response(status=201, response=str(task.task_id))


@app.route('/api/v1/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Возвращает все атрибуты конкретной задачи с id = task_id"""
    try:
        task = Task(task_id)
    except TypeError:
        return Response(status=404, response=f"Task with id {task_id} NOT FOUND")
    else:
        return Response(status=200, response=task.dict())


@app.route('/api/v1/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Удаляет задачу с id = task_id"""
    try:
        task = Task(task_id)
    except ValueError:
        return Response(status=404, response=f'Task with id {task_id} NOT FOUND')
    else:
        task.delete()
        return Response(status=200, response=f"Task with id {task_id} DELETED")


@app.route('/api/v1/tasks/', methods=['PUT'])
def update_task():
    """Обновляет контент и/или статус задачи, необходимо в теле запроса передать task_id
    и атрибут(ы) со значением, которое необоходимо обновить"""
    # Провалидируем тело запроса, если что-то не так, то вернем ошибку 400
    try:
        request_body = dict(UpdateTaskRequestBody(**request.form))
    except ValidationError as e:
        return Response(status=400, response=e.json())
    # Провалидируем id задачи, если такой задачи нет, то вернем ошибку 404
    task_id = request_body.get('task_id')
    try:
        task = Task(task_id)
    except ValueError:
        return Response(status=404, response=f'Task with id {task_id} NOT FOUND')
    # Обновим атрибуты задачи
    if request_body.get('content') is not None:
        task.content = request_body.get('content')
    if request_body.get('status') is not None:
        task.current_status = request_body.get('status')
    return Response(status=200)


if __name__ == '__main__':
    # Закроем пул соединений после завершения работы программы
    atexit.register(close_connection_pool)
    app.run()
