import os
import json
import secrets
import threading
from .models import db
from flask import Flask
from config import Config
from .utils import init_utils
from .logger import init_logger
from flask_migrate import Migrate
from .scheduler import init_scheduler

config_lock = threading.Lock()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    user_config_path = os.path.join(app.instance_path, 'user_config.json')
    logs_dir = os.path.join(app.instance_path, 'logs')
    log_file_path = os.path.join(logs_dir, 'ShowRecorder.log')
    
    if not os.path.exists(app.instance_path):
        os.mkdir(app.instance_path)
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)

    initial_logger = init_logger(log_file_path)
    initial_logger.info("Init logger initialized.")

    if not os.path.exists(user_config_path):
        try:
            with open(user_config_path, 'w') as f:
                secret_key = secrets.token_hex(16)
                default_config = {
                    "SECRET_KEY": secret_key
                }
                json.dump(default_config, f, indent=4)
                app.config['SECRET_KEY'] = secret_key
        except Exception as e:
            initial_logger.error(f"Error creating user config: {e}")
    else:
        try:
            with open(user_config_path, 'r') as f:
                user_config = json.load(f)
                app.config.update(user_config)
        except Exception as e:
            initial_logger.error(f"Error loading user config: {e}")

    try:
        db.init_app(app)
        Migrate(app, db)

        with app.app_context():
            from flask_migrate import upgrade, init, migrate
            migrations_dir = os.path.join(app.instance_path, 'migrations')
            if not os.path.exists(migrations_dir):
                try:
                    init(directory=migrations_dir)
                    migrate(message="Initial migration", directory=migrations_dir)
                    upgrade(directory=migrations_dir)
                except Exception as e:
                    initial_logger.logger.error(f"Error during migrations: {e}")
    except Exception as e:
        initial_logger.error(f"Error initializing the database: {e}")
        
    try:
        init_scheduler(app)
    except Exception as e:
        initial_logger.error(f"Error initilizing scheduler: {e}")

    try:
        init_utils()
    except Exception as e:
        initial_logger.error(f"Error initializing utils: {e}")
    
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    initial_logger.info("Application startup complete.")

    return app