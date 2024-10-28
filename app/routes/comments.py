from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import Comment
from http import HTTPStatus

comments_ns = Namespace('comments', description='Comment operations')

comment_model = comments_ns.model('Comment', {
    'id': fields.Integer(readonly=True),
    'content': fields.String(required=True),
    'created_at': fields.DateTime(readonly=True),
    'task_id': fields.Integer(readonly=True),
    'user_id': fields.Integer(readonly=True)
})


@comments_ns.route('/')
class CommentList(Resource):
    @comments_ns.doc('list_comments')
    @comments_ns.marshal_list_with(comment_model)
    def get(self):
        try:
            comments = Comment.query.all()
            return comments
        except SQLAlchemyError as e:
            comments_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Database error occurred: {str(e)}"
            )
        except Exception as e:
            comments_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An unexpected error occurred: {str(e)}"
            )


@comments_ns.route('/<int:comment_id>')
@comments_ns.param('comment_id', 'The comment identifier')
@comments_ns.response(HTTPStatus.NOT_FOUND, 'Comment not found')
class CommentResource(Resource):
    @comments_ns.doc('get_comment')
    @comments_ns.marshal_with(comment_model)
    def get(self,comment_id):
        try:
            comment = Comment.query.get_or_404(comment_id)
            return comment
        except SQLAlchemyError as e:
            comments_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Database error occurred: {str(e)}"
            )
        except Exception as e:
            comments_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An unexpected error occurred: {str(e)}"
            )

    @comments_ns.doc('update_comment')
    @comments_ns.expect(comment_model)
    @comments_ns.marshal_with(comment_model)
    def put(self,comment_id):
        try:
            comment = Comment.query.get_or_404(comment_id)
            data = request.json
            comment.content = data['content']
            db.session.commit()
            return comment
        except SQLAlchemyError as e:
            db.session.rollback()
            comments_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Database error occurred: {str(e)}"
            )
        except Exception as e:
            db.session.rollback()
            comments_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An unexpected error occurred: {str(e)}"
            )

    @comments_ns.doc('delete_comment')
    @comments_ns.response(HTTPStatus.NO_CONTENT, 'Comment deleted')
    def delete(self, comment_id):
        try:
            comment = Comment.query.get_or_404(id)
            db.session.delete(comment)
            db.session.commit()
            return '', HTTPStatus.NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            comments_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Database error occurred: {str(e)}"
            )
        except Exception as e:
            db.session.rollback()
            comments_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An unexpected error occurred: {str(e)}"
            )
