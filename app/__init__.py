import os
import logging
import secrets
import threading
from .models import db
from flask import Flask
from config import Config
from flask_migrate import Migrate
from .scheduler import init_scheduler
from logging.handlers import RotatingFileHandler

config_lock = threading.Lock()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    user_config_path = os.path.join(app.instance_path, 'user_config.py')
    logs_dir = os.path.join(app.instance_path, 'logs')
    log_file_path = os.path.join(logs_dir, 'ShowRecorder.log')
    
    if not os.path.exists(app.instance_path):
        os.mkdir(app.instance_path)
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)
    
    if not any(isinstance(handler, RotatingFileHandler) for handler in app.logger.handlers):
        handler = RotatingFileHandler(log_file_path, maxBytes=1024*1024*5, backupCount=5)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
    

    if not os.path.exists(user_config_path):
        try:
            with open(user_config_path, 'w') as f:
                secret_key = secrets.token_hex(16)
                f.write(f"SECRET_KEY = '{secret_key}'\n")
                app.config['SECRET_KEY'] = secret_key
        except Exception as e:
            app.logger.error(f"Error creating user config: {e}")
    else:
        app.config.from_pyfile(user_config_path)

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
                    app.logger.error(f"Error during migrations: {e}")
    except Exception as e:
        app.logger.error(f"Error initializing the database: {e}")
        
    try:
        init_scheduler(app)
    except Exception as e:
        app.logger.error(f"Error initilizing scheduler: {e}")
    
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app