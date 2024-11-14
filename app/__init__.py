import os
import secrets
from flask import Flask
from config import Config
from .models import db
from .scheduler import init_scheduler
from flask_migrate import Migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure the instance and output folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # Path for user-specific configuration
    user_config_path = os.path.join(app.instance_path, 'user_config.py')
    
    # Check if user_config.py exists; if not, create it and generate a secret key
    if not os.path.exists(user_config_path):
        with open(user_config_path, 'w') as f:
            # Generate a new secret key
            secret_key = secrets.token_hex(16)
            f.write(f"SECRET_KEY = '{secret_key}'\n")
            app.config['SECRET_KEY'] = secret_key  # Set it in the app config
    else:
        # Load any user-defined settings, including SECRET_KEY if it exists
        app.config.from_pyfile(user_config_path, silent=True)

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    # Run migrations
    with app.app_context():
        from flask_migrate import upgrade, init, migrate
        if not os.path.exists(os.path.join(os.getcwd(), 'migrations')):
            init()
        try:
            migrate(message="Initial migration")
            upgrade()
        except Exception as e:
            print(f"Error applying migrations: {e}")
    
        # Initialize the scheduler
        init_scheduler(app)
    
    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
