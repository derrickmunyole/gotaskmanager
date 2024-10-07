from flask import request
from flask_restx import Namespace, Resource, fields
from app import db
from app.models import Project
from sqlalchemy.exc import SQLAlchemyError
from http import HTTPStatus


project_ns = Namespace('projects', description='Project operations')


project_model = project_ns.model('Project', {
    'id': fields.Integer(readonly=True, description='The project unique identifier'),
    'name': fields.String(required=True, description='The project name'),
    'description': fields.String(description='The project description')
})


@project_ns.route('/')
class ProjectList(Resource):
    @project_ns.doc('list_projects')
    @project_ns.marshal_list_with(project_model)
    def get(self):
        try:
            return Project.query.all()
        except SQLAlchemyError as e:
            project_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An error occurred while retrieving projects"
            )

    @project_ns.doc('create_project')
    @project_ns.expect(project_model)
    @project_ns.marshal_with(project_model, code=201)
    def post(self):
        data = project_ns.payload
        new_project = Project(name=data['name'], description=data.get('description'))
        try:
            db.session.add(new_project)
            db.session.commit()
            return new_project, HTTPStatus.CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            project_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An error occurred while creating the project"
            )


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
