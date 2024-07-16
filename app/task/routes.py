import logging

from flask import Blueprint, request, jsonify
from flask_restx import Namespace, Resource, fields
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import NotFound
from http import HTTPStatus

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
    'id': fields.Integer(description='The unique identifier of a task'),
    'title': fields.String(required=True, description='The task title'),
    'description': fields.String(description='The task description'),
    'due_date': fields.DateTime(description='The due date of the task'),
    'completed_at': fields.DateTime(description='The completion date of the task'),
    'status': fields.String(description='The status of the task'),
    'priority': fields.String(description='The priority of the task')
})

task_list_response = ns.model('TaskListResponse', {
    'success': fields.Boolean(description='Indicates if the request was successful'),
    'tasks': fields.List(fields.Nested(task_model), description='List of tasks')
})

task_create_response = ns.model('TaskCreateResponse', {
    'success': fields.Boolean(description='Indicates if the request was successful'),
    'message': fields.String(description='A message describing the result'),
    'task': fields.Nested(task_model, description='The created task')
})

task_update_model = ns.model('TaskUpdate', {
    'title': fields.String(description='The task title'),
    'description': fields.String(description='The task description'),
    'due_date': fields.String(description='The due date of the task'),
    'completed_at': fields.String(description='The completion date of the task'),
    'status': fields.String(description='The status of the task'),
    'priority': fields.String(description='The priority of the task')
})

task_update_response = ns.model('TaskUpdateResponse', {
    'success': fields.Boolean(description='Indicates if the request was successful'),
    'message': fields.String(description='A message describing the result'),
    'task': fields.Nested(task_model, description='The updated task')
})

tag_ids_model = ns.model('TaskTags', {
    'tag_ids': fields.List(fields.Integer, required=True, description='List of tag IDs')
})

task_assign_project_model = ns.model('TaskAssignToProject', {
    'project_id': fields.Integer(required=True, description='The ID of the project to assign the task to')
})

comment_input_model = ns.model('TaskComments', {
    'content': fields.String(),
})

task_comment_model = ns.model('TaskComments', {

})

task_assign_user_model = ns.model('TaskAssignToUser', {
    'user_id': fields.Integer(required=True, description='The ID of the user to assign the task to')
})


@ns.route('/tasks')
class TaskList(Resource):
    @ns.marshal_with(task_list_response)  # Response is automatically serialized according to the
    # defined model.
    @ns.response(200, 'Ok', task_list_response)
    @ns.response(500, 'Internal server error')
    def get(self):
        try:
            tasks = Task.query.all()

            return {
                'success': True,
                'tasks': [task.to_dict() for task in tasks]
            }, 200
        except SQLAlchemyError as e:
            logger.error("Database error while fetching tasks", exc_info=True)
            return {
                'success': False,
                'error': "Database error occurred. Please try again later."
            }, 500
        except Exception as e:
            logger.error("Unexpected error while fetching tasks", exc_info=True)
            return {
                'success': False,
                'error': "An unexpected error occurred. Please try again later."
            }, 500

    @ns.expect(task_model)
    @ns.response(201, 'Created', task_model)
    @ns.response(500, 'Internal server error')
    def post(self):
        try:
            data = request.get_json()
            title = data.get('title')
            description = data.get('description')

            if not title:
                return {
                    'success': False,
                    'error': 'Title is required'
                }, 400

            new_task = Task(
                title=title,
                description=description
            )

            db.session.add(new_task)
            db.session.commit()

            return {
                'success': True,
                'message': 'Task created successfully',
                'task': new_task.to_dict()
            }, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error("Database error while creating new task", exc_info=True)
            return {
                'success': False,
                'error': "Database error occurred. Please try again later."
            }, 500
        except Exception as e:
            logger.info("Error creating new task", exc_info=e)
            return {'success': False, 'error': str(e)}, 500


@ns.route('/tasks/<int:task_id>')
class TaskUpdate(Resource):
    @ns.expect(task_update_model)
    @ns.response(200, 'Ok', task_update_response)
    @ns.response(404, 'Not found')
    @ns.response(500, 'Internal server error')
    def put(self, task_id):
        try:
            task = Task.query.get(task_id)

            if task is None:
                return jsonify({'success': False, 'message': 'Not found'}), 404

            data = request.get_json()

            for field in ['title', 'description', 'due_date', 'completed_at', 'status', 'priority']:
                if field in data:
                    setattr(task, field, data[field])

            if not task.title:
                return {
                    'success': False,
                    'message': 'Title cannot be empty'
                }, 400

            db.session.commit()
            return {
                'success': True,
                'message': 'Task updated successfully',
                'task': task.to_dict()
            }, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error("Database error while updating task", exc_info=True)
            return {
                'success': False,
                'message': "Database error occurred. Please try again later."
            }, 500
        except Exception as e:
            logger.error("Error updating task", exc_info=e)
            return {
                'success': False,
                'error': str(e)
            }, 500


@ns.route('/<int:task_id>')
class TaskResource(Resource):
    @ns.response(HTTPStatus.NO_CONTENT, 'No Content')
    @ns.response(HTTPStatus.NOT_FOUND, 'Not found')
    @ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error')
    def delete(self, task_id):
        try:
            task = Task.query.get_or_404(task_id)

            db.session.delete(task)
            db.session.commit()

            return '', 204

        except NotFound:
            ns.abort(404, f"Task with id {task_id} not found")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting task with id {task_id}", exc_info=True)
            ns.abort(500, f"An error occurred while deleting the task: {str(e)}")


@ns.route('/tasks/<int:task_id>/tags')
class TaskTags(Resource):
    @ns.expect(tag_ids_model)
    @ns.response(200, 'Tags updated successfully')
    @ns.response(404, 'Task not found')
    @ns.response(400, 'Invalid request')
    @ns.response(500, 'Internal server error')
    def post(self, task_id):
        try:
            data = ns.payload
            tag_ids = data.get('tag_ids', [])

            if not isinstance(tag_ids, list):
                ns.abort(400, 'tag_ids must be a list of integers')

            task = Task.query.get_or_404(task_id)

            tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

            # Check if all provided tag_ids exist
            if len(tags) != len(tag_ids):
                ns.abort(400, 'One or more tag IDs are invalid')

            task.tags = tags
            db.session.commit()

            return {'message': 'Tags updated successfully'}, 200
        except Exception as e:
            logger.error(f"Error assigning tags to task: {str(e)}", exc_info=True)
            ns.abort(500, 'An error occurred while assigning tags')


@ns.route('/tasks/<int:task_id/assign')
class TaskAssignToProject(Resource):
    @ns.doc(params={'task_id': 'The task ID'})
    @ns.expect(task_assign_project_model)
    @ns.response(HTTPStatus.OK, 'Task assigned to project successfully')
    @ns.response(HTTPStatus.NOT_FOUND, 'Task or Project not found')
    @ns.response(HTTPStatus.BAD_REQUEST, 'Invalid input')
    @ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error')
    def post(self, task_id):
        try:
            data = ns.payload
            project_id = data.get('project_id')

            if not project_id:
                return {
                    'success': False,
                    'message': 'Project ID is required'
                }, HTTPStatus.BAD_REQUEST

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
                'message': 'Task assigned to project successfully',
                'data': {
                    'task_id': task.id,
                    'project_id': project.id,
                    'project_name': project.name
                }
            }, HTTPStatus.OK
        except SQLAlchemyError as e:
            db.session.rollback()
            return {
                'success': False,
                'message': 'A database error occurred while assigning the task to the project',
                'error': str(e)
            }, HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': 'An error occurred while assigning the task to the project',
                'error': str(e)
            }, HTTPStatus.INTERNAL_SERVER_ERROR


@ns.route('/tasks/<int:task_id>/comments')
class TaskComments(Resource):
    @ns.expect(comment_input_model)
    @ns.response(HTTPStatus.CREATED, 'Created', task_comment_model)
    @ns.response(HTTPStatus.BAD_REQUEST, 'Bad Request')
    @ns.response(HTTPStatus.NOT_FOUND, 'Not found')
    @ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error')
    def post(self, task_id):
        try:
            data = ns.payload
            content = data.get('content')

            if not content or not content.strip():
                return {
                    'success': False,
                    'message': 'Comment content cannot be empty'
                }, 400

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
                'message': 'Comment added successfully',
                'comment': new_comment
            }, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            return {
                'success': False,
                'message': 'A database error occurred while adding comment',
                'error': str(e)
            }, HTTPStatus.INTERNAL_SERVER_ERROR

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': 'An error occurred while adding the comment',
                'error': str(e)
            }, 500


@ns.route('/tasks/<int:task_id>/assign_user')
class TaskAssignUser(Resource):
    @ns.doc(params={'task_id': 'The task ID'})
    @ns.expect(task_assign_user_model)
    @ns.response(HTTPStatus.OK, 'Task assigned to user successfully')
    @ns.response(HTTPStatus.NOT_FOUND, 'Task or User not found')
    @ns.response(HTTPStatus.BAD_REQUEST, 'Invalid input')
    @ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error')
    def post(self, task_id):
        try:
            data = ns.payload
            user_id = data.get('user_id')

            if not user_id:
                return {
                    'success': False,
                    'message': 'User ID is required'
                }, HTTPStatus.BAD_REQUEST

            task = Task.query.get(task_id)
            if not task:
                return {
                    'success': False,
                    'message': 'Task not found'
                }, HTTPStatus.NOT_FOUND

            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }, HTTPStatus.NOT_FOUND

            task.user = user
            db.session.commit()

            return {
                'success': True,
                'message': 'Task assigned to user successfully',
                'data': {
                    'task_id': task.id,
                    'user_id': user.id,
                    'user_name': user.name
                }
            }, HTTPStatus.OK

        except SQLAlchemyError as e:
            db.session.rollback()
            return {
                'success': False,
                'message': 'A database error occurred while assigning the task',
                'error': str(e)
            }, HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': 'An error occurred while assigning the task',
                'error': str(e)
            }, HTTPStatus.INTERNAL_SERVER_ERROR


