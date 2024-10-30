from sqlalchemy.exc import SQLAlchemyError
from app.aop import log_activity
from app.models import Comment
from app.routes.users import session_required
from app import db


class CommentService:
    @staticmethod
    @session_required
    @log_activity('post', 'comment')
    def post_comment(data, current_user):
        """
        Posts a new comment to the database.

        This method requires the 'content' field in the data dictionary.
        It logs the activity and ensures a session is active before proceeding.
        If successful, the comment is added to the database and committed.

        Args:
            data (dict): A dictionary containing the comment data. Must include 'content'.
            current_user: The user who is posting the comment.

        Returns:
            Comment: The newly created comment object.

        Raises:
            ValueError: If required fields are missing in the data.
            Exception: If a database error occurs or any other error is encountered.
        """
        try:
            if not all(key in data for key in ['content']):
                raise ValueError("Missing required fields")

            comment = Comment(**data)
            db.session.add(comment)
            db.session.commit()
            return comment
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception("Database error occurred") from e
        except Exception as e:
            raise Exception("An error occurred while posting a comment")

    @staticmethod
    @session_required
    @log_activity('update', 'comment')
    def update_comment(comment_id, data, current_user):
        """
        Updates an existing comment in the database.

        This method requires the 'content' field in the data dictionary.
        It logs the activity and ensures a session is active before proceeding.
        If successful, the comment is updated in the database and committed.

        Args:
            comment_id: The ID of the comment to be updated.
            data (dict): A dictionary containing the updated comment data. Must include 'content'.
            current_user: The user who is updating the comment.

        Returns:
            Comment: The updated comment object.

        Raises:
            ValueError: If required fields are missing in the data.
            Exception: If a database error occurs or any other error is encountered.
        """
        try:
            comment = Comment.query.get(comment_id)
            if not all(key in data for key in ['content']):
                raise ValueError("Missing required fields")

            if 'content' in data:
                data.content = data['content']

            db.session.commit()

            return comment
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception("Database error occurred") from e
        except Exception as e:
            raise Exception("An error occurred while updating the comment")
