from http import HTTPStatus

from flask_restx import Namespace, Resource, fields
from sqlalchemy.exc import SQLAlchemyError

from app import db
from .model import Tag

tags_ns = Namespace('tags', description='Tag operations')

tag_model = tags_ns.model('Tag', {
    'id': fields.Integer(readonly=True, description='The tag identifier'),
    'name': fields.String(required=True, description='The tag name'),
})


@tags_ns.route('/')
class TagList(Resource):
    @tags_ns.doc('list_tags')
    @tags_ns.marshal_list_with(tag_model)
    def get(self):
        try:
            return Tag.query.all()
        except SQLAlchemyError as e:
            tags_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Database error occurred: {str(e)}"
            )
        except Exception as e:
            tags_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An unexpected error occurred: {str(e)}"
            )

    @tags_ns.doc('create_tag')
    @tags_ns.expect(tag_model)
    @tags_ns.marshal_with(tag_model, code=HTTPStatus.CREATED)
    def post(self):
        try:
            new_tag = Tag(name=tags_ns.payload['name'])
            db.session.add(new_tag)
            db.session.commit()
            return new_tag, HTTPStatus.CREATED
        except SQLAlchemyError as e:
            db.session.rollback()
            tags_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Database error occurred: {str(e)}"
            )
        except Exception as e:
            tags_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An unexpected error occurred: {str(e)}"
            )


@tags_ns.route('/<int:comment_id>')
@tags_ns.response(HTTPStatus.NOT_FOUND, 'Tag not found')
@tags_ns.param('comment_id', 'The tag identifier')
class TagItem(Resource):
    @tags_ns.doc('get_tag')
    @tags_ns.marshal_with(tag_model)
    def get(self, comment_id):
        try:
            tag = Tag.query.get_or_404(comment_id)
            return tag
        except SQLAlchemyError as e:
            tags_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Database error occurred: {str(e)}"
            )
        except Exception as e:
            tags_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An unexpected error occurred: {str(e)}"
            )

    @tags_ns.doc('update_tag')
    @tags_ns.expect(tag_model)
    @tags_ns.marshal_with(tag_model)
    def put(self, comment_id):
        try:
            tag = Tag.query.get_or_404(comment_id)
            tag.name = tags_ns.payload['name']
            db.session.commit()
            return tag
        except SQLAlchemyError as e:
            db.session.rollback()
            tags_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Database error occurred: {str(e)}"
            )
        except Exception as e:
            tags_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An unexpected error occurred: {str(e)}"
            )

    @tags_ns.doc('delete_tag')
    @tags_ns.response(HTTPStatus.NO_CONTENT, 'Tag deleted')
    def delete(self, comment_id):
        try:
            tag = Tag.query.get_or_404(comment_id)
            db.session.delete(tag)
            db.session.commit()
            return '', HTTPStatus.NO_CONTENT
        except SQLAlchemyError as e:
            db.session.rollback()
            tags_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Database error occurred: {str(e)}"
            )
        except Exception as e:
            tags_ns.abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"An unexpected error occurred: {str(e)}"
            )
