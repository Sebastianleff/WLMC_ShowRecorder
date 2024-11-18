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
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,  # Set to DEBUG for more detailed logs
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),  # Send logs to stderr
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Creating Flask application")
    
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
            print(f"Error applying migrations: {e}")
    
        init_scheduler(app)
    
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app