import logging
from flask_restx import Namespace, Resource, fields
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import Activities
from http import HTTPStatus

logger = logging.getLogger(__name__)
activities_ns = Namespace('Activities', description='Activities operations')
parser = activities_ns.parser()
parser.add_argument('limit', type=int, default=10, help="Number of activities to fetch")

activities_model = activities_ns.model('Activity', {
    'user_id': fields.Integer(required=True),
    'action_type': fields.String(required=True),
    'target_type': fields.String(required=True),
    'target_id': fields.String(required=True),
    'target': fields.Raw(required=False)
})


@activities_ns.route('/recent-activities')
class ActivitiesResource(Resource):

    @activities_ns.marshal_with(activities_model)
    def get(self):
        try:
            args = parser.parse_args()
            limit = args.get('limit', 10)
            activities = Activities.query.order_by(Activities.created_at).limit(limit).all()
            return activities, HTTPStatus.OK
        except SQLAlchemyError as e:
            logger.error(
                "Database error while retrieving recent activities",
                exc_info=e
            )
            return {
                'success': False,
                'error': str(e)
            }, HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            logger.error(
                "Error while fetching activities",
                exc_info=e
            )
            return {
                'success': False,
                'error': str(e)
            }, HTTPStatus.INTERNAL_SERVER_ERROR

    @activities_ns.expect(activities_model)
    def post(self):
        try:
            data = activities_ns.payload
            activity_instance = Activities(
                user_id=data['user_id'],
                action_type=data['action_type'],
                target_type=data['target_type'],
                target_id=data['target_id'],
                details_json=data.get('details', {})
            )
            db.session.add(activity_instance)
            db.session.commit()
            return {
                'message': "Activity created successfully"
            }, HTTPStatus.CREATED
        except SQLAlchemyError as e:
            logger.error(
                "Database error while creating new activity",
                exc_info=e
            )
            return {
                'success': False,
                'error': str(e)
            }, HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            logger.error("Error creating new activity")
            return {
                'success': False,
                'error': str(e)
            }, HTTPStatus.INTERNAL_SERVER_ERROR
