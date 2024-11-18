import os
import secrets
import threading
import logging
from flask import Flask
from config import Config
from .models import db
from .scheduler import init_scheduler
from flask_migrate import Migrate

config_lock = threading.Lock()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    if not os.path.exists(app.instance_path):
        os.mkdir(app.instance_path)
    if not os.path.exists(app.config['OUTPUT_FOLDER']):
        os.mkdir(app.config['OUTPUT_FOLDER'])

    user_config_path = os.path.join(app.instance_path, 'user_config.py')
    
    if not os.path.exists(user_config_path):
        with open(user_config_path, 'w') as f:
            secret_key = secrets.token_hex(16)
            f.write(f"SECRET_KEY = '{secret_key}'\n")
            app.config['SECRET_KEY'] = secret_key
    else:
        app.config.from_pyfile(user_config_path, silent=True)

    # Configure logging
    log_dir = os.path.join(app.instance_path, 'logs')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

    app.logger.info("Initializing database")
    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        from flask_migrate import upgrade, init, migrate
        migrations_dir = os.path.join(app.instance_path, 'migrations')
        if not os.path.exists(migrations_dir):
            init(directory=migrations_dir)
        try:
            migrate(message="Initial migration", directory=migrations_dir)
            upgrade(directory=migrations_dir)
        except Exception as e:
            app.logger.error(f"Error applying migrations: {e}")
    
        app.logger.info("Initializing scheduler")
        init_scheduler(app)
    
    from .routes import main_bp
    app.register_blueprint(main_bp)

    app.logger.info("Application created successfully")
    return app