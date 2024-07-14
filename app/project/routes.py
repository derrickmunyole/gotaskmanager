from flask import Blueprint, request, jsonify
from .model import Project
from app import db
import logging

bp = Blueprint('project', __name__)
logger = logging.getLogger(__name__)


@bp.route('/projects', methods=['GET'])
def get_projects():
    try:
        projects = Project.query.all()

        return jsonify(
            {
                'success': True,
                'projects': projects
            }), 200
    except Exception as e:
        logger.error("Error fetching projects", str(e))
        return jsonify(
            {
                'success': False,
                'error': str(e)
            }), 500


@bp.route('projects', methods=['POST'])
def create_project():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description", None)

    try:
        project = Project(name=name, description=description)
        db.session.add(project)
        db.session.commit()
    except Exception as e:
        logger.error("Error creating project", str(e))
        return jsonify(
            {
                'success': False,
                'error': str(e)
            }), 500

    return jsonify(
        {
            'success': True,
            'message': 'Project created successfully',
            'project': project.id
        }), 200


@bp.route('/projects/<int:project_id>')
def get_project(project_id):
    try:
        project = Project.query.get(project_id)

        if project is None:
            return jsonify(
                {
                    'success': False,
                    'message': 'Project not found',
                }), 404

        return jsonify(
            {
                'success': True,
                'project': project
            }), 200

    except Exception as e:
        logger.error('Error getting project details', exc_info=e)
        return jsonify(
            {
                'success': False,
                'error': str(e)
            }), 500


@bp.route('/update/<int:project_id>', method=['PUT'])
def update_project(project_id):
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")

    try:
        project = Project.query.get(project_id)

        if project is None:
            return jsonify(
                {
                    'success': False,
                    'message': 'Project not found'
                }
            )

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description

        db.session.commit()
        return jsonify(
            {
                "success": True,
                "message": "Project updated successfully"
            }), 200

    except Exception as e:
        logger.error("Error updating project", exc_info=e)
        return jsonify(
            {
                'success': False,
                'error': str(e)
            }), 500


@bp.route('/delete/<int:project_id', methode=['DELETE'])
def delete_project(project_id):
    try:
        project = Project.query.get(project_id)

        if project is None:
            return jsonify(
                {
                    'success': False,
                    'message': 'Project not found'
                }
            )

        db.session.delete(project)
        db.session.commit()
        return jsonify(
            {
                'success': True,
                'message': 'Task successfully deleted'
            }), 200
    except Exception as e:
        logger.error("Error deleting project", exc_info=e)
        return jsonify(
            {
                'success': False,
                'error': str(e)
            }), 500
