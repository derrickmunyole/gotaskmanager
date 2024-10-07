from app import db
from app.models import Session
from datetime import datetime, timezone, timedelta


class SessionManager:
    @staticmethod
    def create_session(user_id, session_id):
        new_session = Session(
            user_id=user_id,
            session_id=session_id,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.session.add(new_session)
        db.session.commit()

    @staticmethod
    def invalidate_session(session_id):
        session = Session.query.filter_by(session_id=session_id).first()
        if session:
            db.session.delete(session)
            db.session.commit()
            return True
        return False

    @staticmethod
    def renew_session(session_id):
        session = Session.query.filter_by(session_id=session_id).first()
        if session:
            session.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            db.session.commit()
            return True
        return False

    @staticmethod
    def is_session_valid(session_id):
        session = Session.query.filter_by(session_id=session_id).first()
        if session and session.expires_at > datetime.now(timezone.utc):
            return True
        return False