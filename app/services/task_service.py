from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.aop import log_activity
from app.models import Task
from app.routes.users import session_required


class TaskService:
    @staticmethod
    @session_required
    @log_activity('create', 'task')
    def create_task(data, current_user):
        """
        Creates a new task and saves it to the database.

        This method attempts to create a new Task object using the provided data,
        add it to the database session, and commit the session. If any error occurs
        during this process, it handles the exception by rolling back the session
        and raising an appropriate exception.

        Args:
            data (dict): A dictionary containing the task data to be used for creating
                         the Task object.

            current_user:

        Returns:
            Task: The newly created Task object.

        Raises:
            Exception: If a database error occurs or any other error is encountered
                       during the task creation process.
        """
        try:
            if not all(key in data for key in ['title']):
                raise ValueError("Required values are missing")

            task = Task(**data)
            db.session.add(task)
            db.session.commit()
            return task
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception("Database error occurred") from e
        except Exception as e:
            raise Exception("An error occurred while creating the task") from e
