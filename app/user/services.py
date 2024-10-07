from app.models import RefreshToken
from app.refreshtoken.services import generate_new_access_token


def refresh_access_token(session_id):
    refresh_token_entry = RefreshToken.query.filter_by(session_id=session_id).first()
    if refresh_token_entry:
        return generate_new_access_token(refresh_token_entry.user_id)
    return None
