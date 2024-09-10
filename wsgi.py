from app import create_app, db
from config import Config
from werkzeug.serving import run_simple

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db
    }


if __name__ == '__main__':
    if Config.is_production():
        socket_path = '/var/www/myapp/myflaskapp.sock'
        run_simple('unix://' + socket_path, None, app)
    else:
        app.run(host='127.0.0.1', port=5000, debug=True)
