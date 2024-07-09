from flask import Blueprint

bp = Blueprint('user', __name__)


@bp.route('/login')
def login():
    return "User Login"
