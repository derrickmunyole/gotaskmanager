from app import create_app, db
from config import Config  # Assuming your Config class is in app/config.py

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db
    }


if __name__ == '__main__':
    if Config.is_production():
        app.run(host='0.0.0.0', port=8080, debug=False)
    else:
        app.run(host='127.0.0.1', port=5000, debug=True)
