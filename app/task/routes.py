from flask import Blueprint, request, jsonify
from .model import Task
from app import db
import logging

bp = Blueprint('task', __name__)
logger = logging.getLogger(__name__)


@bp.route('/tasks', methods=['GET'])
def get_all_tasks():
    tasks = []
    try:
        tasks = Task.query.all()
    except Exception as e:
        logger.info("Error fetching tasks", exc_info=e)
        return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': True, 'tasks': tasks}), 200


@bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description') or None

    try:
        new_task = Task(
            title=title,
            description=description
        )

        db.session.add(new_task)
        db.session.commit()
    except Exception as e:
        logger.info("Error creating new task", exc_info=e)
        return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': True, 'message': 'Task created'}), 201


@bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    due_date = data.get('due_date')
    completed_at = data.get('completed_at')
    status = data.get('status')
    priority = data.get('priority')

    try:
        task = Task.query.get(task_id)

        if task is None:
            return jsonify({'success': False, 'message': 'Task not found'}), 404

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if due_date is not None:
            task.due_date = due_date
        if completed_at is not None:
            task.completed_at = completed_at
        if status is not None:
            task.status = status
        if priority is not None:
            task.priority = priority

        db.session.commit()
        return jsonify({'success': True, 'message': 'Task updated successfully'}), 200
    except Exception as e:
        logger.error("Error updating task", exc_info=e)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        task = Task.query.get(task_id)

        if task is None:
            return jsonify({'success': False, 'message': 'Task not found'}), 404

        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task successfully deleted'}), 200
    except Exception as e:
        logger.error("Error deleting task", exc_info=e)
        return jsonify({'success': False, 'error': str(e)}), 500

