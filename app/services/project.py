from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app import db
from app.aop import log_activity
from app.models import Project
from app.routes.users import session_required


class ProjectService:
    @staticmethod
    @session_required
    @log_activity('create', 'project')
    def create_project(data, current_user):
        """
        Creates a new project using the provided data and associates it with the current user.

        This method requires a session and logs the activity of creating a project.

        Args:
            data (dict): A dictionary containing the project details. Must include the 'name' key.
            current_user (User): The user who is creating the project.

        Returns:
            Project: The newly created project object.

        Raises:
            ValueError: If required values are missing from the data.
            Exception: If a database error occurs or any other error is encountered during project creation.
        """
        try:
            if not all(key in data for key in ['name']):
                raise ValueError("Required values are missing")

            project = Project(**data)
            db.session.add(project)
            db.session.commit()
            return project
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception("Database error occurred") from e
        except Exception as e:
            raise Exception("An error occurred while creating the project") from e

    @staticmethod
    @session_required
    @log_activity('update', 'project')
    def update_project(project_id, data, current_user):
        """
        Updates the specified project with the provided data.

        This method retrieves a project by its ID and updates its fields based on the
        provided data dictionary. Only fields that exist on the Project model and are
        instances of InstrumentedAttribute will be updated. Fields that do not meet
        these criteria will be ignored.

        Args:
            project_id (int): The ID of the project to update.
            data (dict): A dictionary containing field-value pairs to update the project with.
            current_user (User): The user performing the update operation.

        Returns:
            dict: A dictionary containing the updated project, a list of updated fields,
                  and a list of ignored fields.

        Raises:
            ValueError: If no project is found with the given project_id.
            Exception: If a database error occurs or any other error is encountered during the update process.
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                raise ValueError("No matching project found")

            updated_fields = []
            ignored_fields = []

            for field, value in data.items():
                if hasattr(Project, field) and isinstance(getattr(Project, field), InstrumentedAttribute):
                    setattr(project, field, value)
                    updated_fields.append(field)
                else:
                    ignored_fields.append(field)

            db.session.commit()

            result = {
                'project': project,
                'updated_fields': updated_fields,
                'ignored_fields': ignored_fields
            }

            return result
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception("Database error occurred") from e
        except Exception as e:
            raise Exception("An error occurred while updating the project")

    @staticmethod
    @session_required
    @log_activity('archive', 'project')
    def archive_project(project_id, data, current_user):
        try:
            project = Project.query.get(project_id)
            if not project:
                raise ValueError("No matching project found")

            project.is_archived = True
            db.session.commit()
            return project
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception("Database error occurred while archiving project") from e
        except Exception as e:
            raise Exception("An error occurred while archiving project") from e
