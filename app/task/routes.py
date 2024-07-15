import logging

from flask import Blueprint, request, jsonify
from flask_restx import Namespace, Resource, fields

from app import db
from app.tag.model import Tag
from .model import Task
from ..project.model import Project
from ..comment.model import Comment
from ..user.model import User

bp = Blueprint('task', __name__)
ns = Namespace('task', path='task')
logger = logging.getLogger(__name__)

task_model = ns.model('Task', {
    'title': fields.String(required=True, description='The task title'),
    'description': fields.String(description='The task description')
})

task_update_model = ns.model('TaskUpdate', {
    'title': fields.String(description='The task title'),
    'description': fields.String(description='The task description'),
    'due_date': fields.String(description='The due date of the task'),
    'completed_at': fields.String(description='The completion date of the task'),
    'status': fields.String(description='The status of the task'),
    'priority': fields.String(description='The priority of the task')
})


@ns.route('/tasks')
class TaskList(Resource):
    def get(self):
        try:
            tasks = Task.query.all()
        except Exception as e:
            logger.info("Error fetching tasks", exc_info=e)
            return {
                'success': False,
                'error': str(e)
            }, 500

        return {
            'success': True,
            'tasks': [task.to_dict() for task in tasks]
        }, 200

    @ns.expect(task_model)
    def post(self):
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


@ns.route('/tasks/<int:task_id>')
class TaskUpdate(Resource):
    @ns.expect(task_update_model)
    def put(self, task_id):
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
            return {
                'success': True,
                'message': 'Task updated successfully'
            }, 200
        except Exception as e:
            logger.error("Error updating task", exc_info=e)
            return {
                'success': False,
                'error': str(e)
            }, 500


@ns.route('/<int:task_id>')
class TaskResource(Resource):
    def delete(self, task_id):
        try:
            task = Task.query.get(task_id)

            if task is None:
                return {
                    'success': False,
                    'message': 'Task not found'
                }, 404

            db.session.delete(task)
            db.session.commit()
            return {
                'success': True,
                'message': 'Task successfully deleted'
            }, 200
        except Exception as e:
            logger.error("Error deleting task", exc_info=e)
            return {
                'success': False,
                'error': str(e)
            }, 500


@ns.route('/tasks/<int:task_id>/tags')
class TaskTags(Resource):
    def post(self, task_id):
        data = request.get_json()
        tag_ids = data.get('tag_ids', [])

        task = Task.query.get(task_id).first()
        if not task:
            return {
                'success': False,
                'message': 'Task not found'
            }, 404

        tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
        task.tags = tags
        db.session.commit()

        return {
            'success': True,
            'message': 'Tags updated successfully'
        }


@ns.route('/tasks/<int:task_id/assign')
class TaskAssign(Resource):
    def post(self, task_id):
        data = request.get_json()
        project_id = data.get('project_id')

        task = Task.query.get(task_id)
        if not task:
            return {
                'success': False,
                'message': 'Task not found'
            }, 404

        project = Project.query.get(project_id)
        if not project:
            return {
                'success': False,
                'message': 'Project not found'
            }, 404

        task.project = project
        db.session.commit()
        return {
            'success': True,
            'message': 'Task assigned to project successfully'
        }


@ns.route('/tasks/<int:task_id>/comments')
class TaskComments(Resource):
    def post(self, task_id):
        data = request.get_json()
        content = data.get('content')

        task = Task.query.get(task_id)
        if not task:
            return {
                'success': False,
                'message': 'Task not found'
            }, 404

        new_comment = Comment(content=content, task=task)
        db.session.add(new_comment)
        db.session.commit()

        return {
            'success': True,
            'message': 'Comment added successfully'
        }, 200


@ns.route('/tasks/<int:task_id>/assign_user')
class TaskAssignUser(Resource):
    def post(self, task_id):
        data = request.get_json()
        user_id = data.get('user_id')

        user = User.query.get(user_id)
        if not user:
            return {
                'success': False,
                'message': 'Us not found'
            }, 404

        task = Task.query.get(task_id)
        if not task:
            return {
                'success': False,
                'message': 'Task not found'
            }, 404

        task.user = user
        db.session.commit()

        return {
            'success': True,
            'message': 'Task assigned to user successfully'
        }, 200
