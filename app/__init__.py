import os
from flask import Flask
from config import Config
from .models import db
from .scheduler import init_scheduler
from flask_migrate import Migrate, upgrade, init

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate = Migrate(app, db)

    with app.app_context():
        if not os.path.exists(os.path.join(os.getcwd(), 'migrations')):
            init()
            migrate(message="Initial migration")
            upgrade()

        init_scheduler(app)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
