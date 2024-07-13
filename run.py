from app import create_app, db
from app.user.model import User
from app.task.model import Task
from app.project.model import Project

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Task': Task,
        'project': Project
    }


if __name__ == '__main__':
    app.run(debug=True)
