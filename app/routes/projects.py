import logging
from http import HTTPStatus

from flask_restx import Namespace, Resource, fields
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Project
from app.services.project import ProjectService

project_ns = Namespace('projects', description='Project operations')
logger = logging.getLogger(__name__)

project_model = project_ns.model('Project', {
    'id': fields.Integer(readonly=True, description='The project unique identifier'),
    'name': fields.String(required=True, description='The project name'),
    'description': fields.String(description='The project description'),
    'duration': fields.Integer(description='The project duration'),
    'deadline': fields.Integer(description='The project deadline'),
    'status': fields.String(description='The project status'),
    'created_at': fields.DateTime(descripton='The project creation time'),
    'progress': fields.Integer(description='The percentage of project completion')
})


@project_ns.route('')
class ProjectList(Resource):
    @project_ns.doc('list_projects')
    @project_ns.marshal_list_with(project_model)
    def get(self):
        try:
            projects = Project.query.all()

            if not projects:
                project_ns.abort(HTTPStatus.NOT_FOUND, "Projects not found")
            return projects
        except SQLAlchemyError as e:
            project_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An error occurred while retrieving projects"
            )

    @project_ns.doc('create_project')
    @project_ns.expect(project_model)
    @project_ns.marshal_with(project_model)
    def post(self):
        try:
            data = project_ns.payload
            new_project = ProjectService.create_project(data)
            return {
                'success': True,
                'message': 'Project created successfully',
                'task': new_project
            }, HTTPStatus.CREATED
        except ValueError as e:
            logger.info("Error creating new project", exc_info=e)
            return {
                'success': False
            }, HTTPStatus.BAD_REQUEST
        except Exception as e:
            logger.info("Error creating new project", exc_info=e)
            return {
                'success': False
            }, HTTPStatus.INTERNAL_SERVER_ERROR


@project_ns.route('/<int:project_id>')
@project_ns.response(HTTPStatus.NOT_FOUND, 'Project not found')
@project_ns.param('project_id', 'The project identifier')
class ProjectItem(Resource):
    @project_ns.doc('get_project')
    @project_ns.marshal_with(project_model)
    def get(self, project_id):
        try:
            project = Project.query.get(project_id)
            if project is None:
                project_ns.abort(HTTPStatus.NOT_FOUND, "Project not found")
            return project
        except SQLAlchemyError as e:
            project_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An error occurred while retrieving the project"
            )

    @project_ns.doc('update_project')
    @project_ns.expect(project_model)
    @project_ns.marshal_with(project_model)
    def put(self, project_id):
        try:
            project = Project.query.get(project_id)
            if project is None:
                project_ns.abort(HTTPStatus.NOT_FOUND, "Project not found")

            data = project_ns.payload
            project.name = data['name']
            project.description = data.get('description')

            db.session.commit()
            return project
        except SQLAlchemyError as e:
            db.session.rollback()
            project_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An error occurred while updating the project"
            )

    @project_ns.doc('delete_project')
    @project_ns.response(HTTPStatus.NO_CONTENT, 'Project deleted')
    def delete(self, project_id):
        try:
            project = Project.query.get(project_id)
            if project is None:
                project_ns.abort(HTTPStatus.NOT_FOUND, "Project not found")

            db.session.delete(project)
            db.session.commit()
            return '', HTTPStatus.NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            project_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An error occurred while deleting the project"
            )


@project_ns.route('/<int:project_id>/archive')
class ArchiveProject(Resource):
    @project_ns.doc('archive_project')
    @project_ns.response(HTTPStatus.OK, 'Project archived successfully')
    @project_ns.response(HTTPStatus.NOT_FOUND, 'Project not found')
    @project_ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error')
    def post(self, project_id):
        try:
            ProjectService.archive_project(project_id)
            return {'message': 'Project archived successfully'}, HTTPStatus.OK
        except ValueError:
            logger.info("Error while archiving project", exc_info=True)
            return {'message': 'Project not found'}, HTTPStatus.NOT_FOUND
        except Exception:
            logger.error(f"Error archiving project {project_id}", exc_info=True)
            return {'message': 'An error occurred while archiving the project'}, HTTPStatus.INTERNAL_SERVER_ERROR
