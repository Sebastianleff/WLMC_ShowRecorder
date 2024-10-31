import os
from flask import Flask
from config import Config
from .models import db
from .scheduler import init_scheduler
from flask_migrate import Migrate, upgrade, init

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Check if the 'migrations' folder exists; if not, initialize and apply migrations
    with app.app_context():
        if not os.path.exists(os.path.join(os.getcwd(), 'migrations')):
            init()  # Initialize the migrations folder
            migrate(message="Initial migration")  # Create the initial migration script
            upgrade()  # Apply the migration to the database

        # Initialize the scheduler
        init_scheduler(app)

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
