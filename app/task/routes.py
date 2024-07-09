from flask import Blueprint

bp = Blueprint('task', __name__)


@bp.route('/tasks')
def tasks():
    return "Task List"
